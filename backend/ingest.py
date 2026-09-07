import os
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DOCS_DIR = os.path.join(BASE_DIR, "guideline_docs")  # holds who/ and nice/ subfolders

# Chunks are embedded in larger batches now than before - sentence-transformers
# runs in-process (no network round trip per batch like Ollama did), so bigger
# batches amortize overhead instead of adding risk. Lower this back down if
# you're on a machine with very limited RAM and it struggles.
BATCH_SIZE = 256


def find_pdf_files(root_dir: str) -> list[str]:
    pdf_files = []
    for current_dir, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(current_dir, filename))
    return sorted(pdf_files)


def load_pdf_documents(pdf_files: list[str]):
    documents = []
    failures = []

    for index, pdf_path in enumerate(pdf_files, start=1):
        rel_path = os.path.relpath(pdf_path, DOCS_DIR)
        print(f"   [{index}/{len(pdf_files)}] loading {rel_path}")

        try:
            documents.extend(PyPDFLoader(pdf_path).load())
        except Exception as exc:
            failures.append((rel_path, str(exc)))
            print(f"      WARNING: skipped {rel_path}: {exc}")

    return documents, failures


def ingest():
    if not os.path.isdir(DOCS_DIR):
        raise FileNotFoundError(f"Create this folder and drop PDFs into it: {DOCS_DIR}")

    print(f"Loading PDFs from {DOCS_DIR} (including subfolders)...")
    pdf_files = find_pdf_files(DOCS_DIR)
    print(f"   Found {len(pdf_files)} PDF files.")

    if not pdf_files:
        print("No PDFs found. Add guideline PDFs under guideline_docs/who or guideline_docs/nice.")
        return

    documents, failures = load_pdf_documents(pdf_files)
    print(f"   Loaded {len(documents)} pages.")

    if len(documents) == 0:
        print("No PDF pages were loaded. Check guideline_docs/who and guideline_docs/nice contain .pdf files.")
        return

    if failures:
        print(f"   Skipped {len(failures)} PDF files that could not be loaded.")

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    total = len(chunks)
    print(f"   Created {total} chunks.")

    # Must be the EXACT same model AND settings as rag_engine.py uses at
    # query time. normalize_embeddings=True + cosine space (below) is
    # what makes Chroma's relevance scores land in a real 0-1 range -
    # without both, scores come out as nonsensical negative numbers and
    # score_threshold filtering never works right, regardless of what
    # threshold value you pick.
    print("Loading sentence-transformers embeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"batch_size": 64, "normalize_embeddings": True},
    )

    print(f"Embedding in batches of {BATCH_SIZE} and writing to Chroma...")
    print(f"   Total batches: {(total + BATCH_SIZE - 1) // BATCH_SIZE}")

    vector_store = None
    start_time = time.time()
    processed = 0

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_start = time.time()

        if vector_store is None:
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=CHROMA_DIR,
                collection_metadata={"hnsw:space": "cosine"},
            )
        else:
            vector_store.add_documents(batch)

        processed += len(batch)
        batch_time = time.time() - batch_start
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        remaining = (total - processed) / rate if rate > 0 else 0

        print(
            f"   [{processed}/{total}] batch took {batch_time:.1f}s | "
            f"elapsed {elapsed/60:.1f} min | "
            f"est. remaining {remaining/60:.1f} min"
        )

    print(f"Ingestion complete in {(time.time()-start_time)/60:.1f} minutes. Stored at: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest()