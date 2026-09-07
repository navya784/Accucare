import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Loads OPENROUTER_API_KEY from your local .env file. On a deployment
# platform (Render, etc.) this line is harmless - env vars are set
# directly in the platform's dashboard instead, and load_dotenv() just
# finds no .env file there and does nothing.
load_dotenv()

# Finds the chroma_db path inside your new backend folder structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

if not os.path.isdir(CHROMA_DIR):
    print(f"WARNING: Chroma database not found at {CHROMA_DIR}. Run `python backend\\ingest.py` first.")

print("Connecting to Modular Chroma Database Core...")
# Local, free, no API key or server needed - runs in-process on CPU.
# normalize_embeddings=True makes every vector unit-length, which - paired
# with the cosine space set below - is what makes Chroma's relevance
# scores land in a real 0-1 range. Without both of these, Chroma falls
# back to raw L2 distance math that produces nonsensical negative
# "relevance scores," which is why score_threshold was never matching
# anything regardless of what number was tried.
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True},
)
vector_store = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_metadata={"hnsw:space": "cosine"},
)

# Pull a wider pool, then filter by relevance score so an unrelated PDF
# (e.g. a dementia guideline showing up for a hypertension question)
# doesn't get passed to the LLM as "trusted context." With normalized
# embeddings + cosine space (see above), scores are now genuinely 0-1,
# so this threshold means something real again. Start at 0.4 and adjust
# after testing with real questions - raise it if irrelevant guidelines
# start showing up, lower it if relevant ones are still getting filtered.
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 24, "score_threshold": 0.4},
)

print("Connecting to OpenRouter (Llama 3.1)...")
llm = ChatOpenAI(
    model ="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.1,
    max_tokens=2048,  # raised from 600 - some free/reasoning-style models spend a chunk of the token
                      # budget on hidden internal reasoning before writing the visible answer, so a low
                      # cap can leave nothing left for actual output, producing an empty/near-empty result
)


def format_docs(docs):
    """Format retrieved chunks for the prompt, using the filename and the
    REAL page number from PyPDFLoader's metadata (0-indexed, so +1 for the
    human-readable page). This gives the LLM an actual page to cite instead
    of needing to invent one."""
    formatted = []
    for doc in docs:
        source_path = doc.metadata.get("source", "Guideline Document")
        filename = os.path.basename(source_path)
        page = doc.metadata.get("page")
        page_label = f", page {page + 1}" if page is not None else ""
        formatted.append(f"[Source: {filename}{page_label}]\n{doc.page_content}")
    return "\n\n".join(formatted)


def clean_sources(docs):
    """Return a deduplicated, sorted list of 'filename (page X)' entries."""
    entries = set()
    for doc in docs:
        filename = os.path.basename(doc.metadata.get("source", "Guideline Document"))
        page = doc.metadata.get("page")
        entries.add(f"{filename} (page {page + 1})" if page is not None else filename)
    return sorted(entries)

CLINICAL_PROMPT_TEMPLATE = """You are an advanced medical assistant supporting a licensed physician. You are provided with detailed clinical input data and trusted medical literature contexts.

Generate a highly detailed, comprehensive clinical report following the strict schema structure below. 
CRITICAL RULES:
- Rely ONLY on the provided context evidence text chunks. If the provided literature does not contain clear evidence for an item, state "Insufficient data in local trusted guidelines." Do not hallucinate or invent medical details.
- Extract and use the SPECIFIC details present in the context (drug names, dosages, step order, thresholds, criteria) rather than summarizing vaguely. If the context contains concrete detail, your answer should too.
- When citing a source, cite the document name AND page number exactly as shown in the [Source: ...] tag for the chunk you drew from. Never alter, guess, or invent a page number that differs from what appears in that tag.

### TRUSTED CLINICAL CONTEXT SOURCE MATERIAL:
{context}

### PATIENT CASE FILE METRICS:
- Name: {patient_name}
- Age / Gender: {age} / {gender}
- History: {medical_history}
- Current Presentation Symptoms: {current_symptoms}
- Vitals Matrix: BP: {bp}, HR: {hr} bpm, Temp: {temp}F, SpO2: {spo2}%
- Laboratory Diagnostics Data: {lab_results}
- Diagnostic Imaging Data: {imaging_findings}
- Raw Clinical Notes: {doctor_notes}

Your output report MUST cleanly separate into these headers:
1. CLINICAL SUMMARY
2. LABORATORY & IMAGING INTERPRETATION
3. DIFFERENTIAL DIAGNOSIS (Ranked by severity risks)
4. RECOMMENDED DIAGNOSTIC WORKUP (Additional tests/imaging)
5. EVIDENCE-BASED TREATMENT OPTIONS
6. SPECIFIC MEDICATION SUGGESTIONS (Include dosages, contraindications based on patient profile)
7. EMERGENCY WARNING SIGNS & RISKS
8. FOLLOW-UP & MONITORING STRATEGY
9. CITED CLINICAL REFERENCES

REQUIRED PHYSICIAN DISCLAIMER:
"DISCLAIMER: This report is a synthetic generated data summary derived from indexed clinical guidelines to support decision workflows. The final diagnostic verification, prescription authorization, and primary treatment plan belong exclusively to the attending licensed physician."

Provide the structured report output below:
Answer:"""

prompt = ChatPromptTemplate.from_template(CLINICAL_PROMPT_TEMPLATE)

def run_clinical_rag(patient_data: dict) -> str:
    search_query = f"{patient_data['current_symptoms']} {patient_data.get('medical_history', '')}"
    retrieved_docs = retriever.invoke(search_query)
    print(f"DEBUG: retrieved {len(retrieved_docs)} documents for query: {search_query!r}")
    formatted_context = format_docs(retrieved_docs)
    
    prompt_inputs = {
        "context": formatted_context,
        "patient_name": patient_data["patient_name"],
        "age": patient_data["age"],
        "gender": patient_data["gender"],
        "medical_history": patient_data.get("medical_history") or "None Reported",
        "current_symptoms": patient_data["current_symptoms"],
        "bp": patient_data["vitals"]["blood_pressure"],
        "hr": patient_data["vitals"]["pulse_rate"],
        "temp": patient_data["vitals"]["temperature"],
        "spo2": patient_data["vitals"]["oxygen_saturation"],
        "lab_results": patient_data.get("lab_results") or "None provided",
        "imaging_findings": patient_data.get("imaging_findings") or "None provided",
        "doctor_notes": patient_data.get("doctor_notes") or "None provided"
    }
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(prompt_inputs)