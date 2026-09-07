import os
import time
import shutil

# Keep CPU/thread memory usage predictable on small Railway instances.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DOCS_DIR = os.path.join(BASE_DIR, "guideline_docs")

# Number of chunks sent to Chroma at a time.
# Keep this modest for Railway's limited RAM.
ADD_BATCH_SIZE = 64

# Number of texts sentence-transformers embeds internally at once.
EMBED_BATCH_SIZE = 16

# Marker is created only after the ENTIRE ingestion succeeds.
COMPLETE_MARKER = os.path.join(CHROMA_DIR, ".ingestion_complete")


def find_pdf_files(root_dir: str) -> list[str]:
    pdf_files = []

    for current_dir, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(current_dir, filename))

    return sorted(pdf_files)


def create_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "batch_size": EMBED_BATCH_SIZE,
            "normalize_embeddings": True,
        },
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )

    return vector_store


def ingest():
    if not os.path.isdir(DOCS_DIR):
        raise FileNotFoundError(
            f"Create this folder and add PDFs: {DOCS_DIR}"
        )

    pdf_files = find_pdf_files(DOCS_DIR)

    print(f"Loading PDFs from {DOCS_DIR} (including subfolders)...")
    print(f"   Found {len(pdf_files)} PDF files.")

    if not pdf_files:
        raise RuntimeError(
            "No PDFs found under backend/guideline_docs."
        )

    # ---------------------------------------------------------
    # Fresh rebuild
    #
    # If the previous ingestion was killed halfway through,
    # the Chroma directory may contain a partial database.
    # Delete it before rebuilding so we never mix partial and
    # complete datasets.
    # ---------------------------------------------------------
    if os.path.isdir(CHROMA_DIR):
        print("Removing previous/partial Chroma database...")
        shutil.rmtree(CHROMA_DIR)

    os.makedirs(CHROMA_DIR, exist_ok=True)

    print(
        "Loading sentence-transformers embeddings "
        "(all-MiniLM-L6-v2)..."
    )

    vector_store = create_vector_store()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    pending_chunks = []

    total_pages = 0
    total_chunks = 0
    total_added = 0
    failed_files = []

    start_time = time.time()

    print("Beginning memory-efficient ingestion...")

    # ---------------------------------------------------------
    # Process ONE PDF at a time and ONE PAGE at a time.
    #
    # This is the major RAM-saving change. We never keep all
    # 14,688 pages / 35,116 chunks in memory.
    # ---------------------------------------------------------
    for pdf_index, pdf_path in enumerate(pdf_files, start=1):

        rel_path = os.path.relpath(pdf_path, DOCS_DIR)

        print(
            f"[{pdf_index}/{len(pdf_files)}] loading {rel_path}"
        )

        try:
            loader = PyPDFLoader(pdf_path)

            # lazy_load() prevents the entire PDF from being
            # loaded into RAM at once.
            for page_doc in loader.lazy_load():

                total_pages += 1

                page_chunks = splitter.split_documents(
                    [page_doc]
                )

                pending_chunks.extend(page_chunks)
                total_chunks += len(page_chunks)

                # Write small batches to Chroma.
                while len(pending_chunks) >= ADD_BATCH_SIZE:

                    batch = pending_chunks[:ADD_BATCH_SIZE]
                    pending_chunks = pending_chunks[
                        ADD_BATCH_SIZE:
                    ]

                    vector_store.add_documents(batch)

                    total_added += len(batch)

                    elapsed = time.time() - start_time

                    print(
                        f"   Added {total_added} chunks | "
                        f"pages {total_pages} | "
                        f"elapsed {elapsed / 60:.1f} min"
                    )

                # Explicitly release page-level objects.
                del page_chunks
                del page_doc

            del loader

        except Exception as exc:
            failed_files.append((rel_path, str(exc)))

            print(
                f"   WARNING: skipped {rel_path}: {exc}"
            )

    # ---------------------------------------------------------
    # Write final partial batch.
    # ---------------------------------------------------------
    if pending_chunks:

        vector_store.add_documents(pending_chunks)

        total_added += len(pending_chunks)

        pending_chunks.clear()

    # ---------------------------------------------------------
    # Report failures.
    # ---------------------------------------------------------
    if failed_files:

        print(
            f"WARNING: {len(failed_files)} PDF files failed."
        )

        for rel_path, error in failed_files:
            print(f"   FAILED: {rel_path}")
            print(f"      {error}")

    # ---------------------------------------------------------
    # Safety check.
    #
    # If nothing was actually stored, do NOT mark ingestion
    # complete.
    # ---------------------------------------------------------
    if total_added == 0:

        raise RuntimeError(
            "No chunks were written to Chroma. "
            "The ingestion is not complete."
        )

    elapsed_minutes = (
        time.time() - start_time
    ) / 60

    print()
    print("==============================================")
    print("INGESTION COMPLETE")
    print("==============================================")
    print(f"Pages processed: {total_pages}")
    print(f"Chunks created:  {total_chunks}")
    print(f"Chunks stored:   {total_added}")
    print(f"Failed PDFs:     {len(failed_files)}")
    print(f"Time:            {elapsed_minutes:.1f} minutes")
    print(f"Chroma path:     {CHROMA_DIR}")
    print("==============================================")

    # ---------------------------------------------------------
    # Only now do we create the completion marker.
    # Railway will use this marker to avoid re-ingesting on
    # every normal restart.
    # ---------------------------------------------------------
    with open(COMPLETE_MARKER, "w", encoding="utf-8") as f:
        f.write(
            "AccuCare guideline ingestion completed successfully.\n"
        )


if __name__ == "__main__":
    ingest()