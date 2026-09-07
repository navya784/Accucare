import os
import re
import json
import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.app.services.rag_engine import retriever, llm, format_docs, clean_sources
from backend.app.database import get_db
from backend.app import models
from backend.app.auth import get_current_doctor

router = APIRouter()


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    chat_history: List[ChatTurn] = Field(default_factory=list)
    session_id: Optional[str] = None  # groups messages into one conversation in the DB


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    unverified_citation_warning: bool = False


CHAT_PROMPT_TEMPLATE = """You are a clinical decision support tool used by a doctor at the point of care. The doctor is looking up official guideline content on a clinical topic - answer as a lookup of the guidelines, regardless of how the question is phrased (formal, casual, first-person, shorthand). Never refuse or deflect a question just because it is phrased informally (e.g. "I have fever, what to do?") - treat it exactly the same as "what is the guideline-recommended management of fever?" and answer from the retrieved context. Do not comment on whether the phrasing sounds like a patient or a doctor - just answer the clinical question using the trusted context below.

- Be specific and thorough: include the concrete detail from the context (drug names, doses, step order, thresholds, criteria) rather than a vague one-line summary. A doctor needs the actual guidance, not just that guidance exists.
- Cite the guideline source document AND page number exactly as shown in the [Source: ...] tag for the chunk you drew from, using that same [Source: filename, page X] format inline in your answer near each fact you use. Never alter, guess, or invent a page number that differs from what appears in that tag.
- NEVER cite an organization, guideline, or document name that is not one of the filenames shown in the [Source: ...] tags of the TRUSTED CLINICAL CONTEXT below. Do not cite "GINA", "WHO", "CDC", or any other body from memory unless that exact source appears in the context provided to you. If you know a fact from general medical knowledge but it is not present in the context below, do not state it as guideline-sourced - either omit it or clearly say it is general knowledge not found in the local trusted guidelines.
- Only say "Insufficient data in local trusted guidelines" if the retrieved context genuinely does not address the clinical topic asked about. Never say this because of how the question was phrased.

Conversation so far:
{history}

TRUSTED CLINICAL CONTEXT:
{context}

Doctor's question: {question}

Answer:"""

chat_prompt = ChatPromptTemplate.from_template(CHAT_PROMPT_TEMPLATE)


def format_history(chat_history: List[ChatTurn]) -> str:
    if not chat_history:
        return "(no prior messages)"
    return "\n".join(f"{turn.role}: {turn.content}" for turn in chat_history)


# Matches "[Source: filename.pdf, page 12]" or "[Source: filename.pdf]" —
# whatever citation tags the LLM actually included in its written answer.
CITATION_PATTERN = re.compile(r"\[Source:\s*([^\]]+)\]")


def verify_citations(answer: str, retrieved_docs) -> tuple[List[str], bool]:
    """Cross-check every [Source: ...] tag the LLM wrote against the
    filenames that were ACTUALLY retrieved from ChromaDB for this
    question. The LLM can write a citation tag that looks legitimate
    (e.g. "[Source: GINA 2020, page 13]") even when nothing by that name
    was ever retrieved - that's a fabricated citation, not a real one,
    and it must not be trusted just because it's formatted correctly.

    Returns (verified_sources, has_unverified_citation).
    """
    real_filenames = {
        os.path.basename(doc.metadata.get("source", "")).lower()
        for doc in retrieved_docs
    }

    cited_raw = [match.strip() for match in CITATION_PATTERN.findall(answer)]
    verified = set()
    has_unverified = False

    for citation in cited_raw:
        filename_part = citation.split(",")[0].strip().lower()
        if any(filename_part in real or real in filename_part for real in real_filenames if real):
            verified.add(citation)
        else:
            has_unverified = True

    if verified:
        return sorted(verified), has_unverified

    # No citation tags matched a real retrieved document at all -
    # fall back to listing what was actually retrieved, and still
    # flag that the written citations couldn't be verified.
    return clean_sources(retrieved_docs), (has_unverified or bool(cited_raw))


@router.post("/api/v1/clinical/chat", response_model=ChatResponse)
async def clinical_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_doctor: models.DoctorAccount = Depends(get_current_doctor),
):
    try:
        retrieved_docs = retriever.invoke(request.question)
        context = format_docs(retrieved_docs)

        chain = chat_prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "history": format_history(request.chat_history),
            "context": context,
            "question": request.question,
        })

        sources, unverified = verify_citations(answer, retrieved_docs)

        # --- Phase 3: persist this exchange to the database ---
        # Phase 4: now tied to the logged-in doctor's account
        session_id = request.session_id or str(uuid.uuid4())
        db.add(models.ChatHistory(
            doctor_id=current_doctor.id,
            session_id=session_id,
            role="user",
            content=request.question,
        ))
        db.add(models.ChatHistory(
            doctor_id=current_doctor.id,
            session_id=session_id,
            role="assistant",
            content=answer,
            sources_json=json.dumps(sources),
        ))
        db.commit()
        # --- end persistence ---

        return ChatResponse(answer=answer, sources=sources, unverified_citation_warning=unverified)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fault inside chat pipeline: {str(e)}"
        )