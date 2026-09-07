import os
import time
import shutil
import gc

# Keep CPU/thread memory usage predictable on a small Railway instance.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DOCS_DIR = os.path.join(BASE_DIR, "guideline_docs")


# ============================================================
# MEMORY / BATCH SETTINGS
# ============================================================

# Number of chunks written to Chroma at one time.
ADD_BATCH_SIZE = 64

# Number of texts sentence-transformers embeds internally.
# Keep this small for Railway's limited RAM.
EMBED_BATCH_SIZE = 16


# Marker is created ONLY after the complete ingestion succeeds.
COMPLETE_MARKER = os.path.join(
    CHROMA_DIR,
    ".ingestion_complete"
)


# ============================================================
# FIND PDF FILES
# ============================================================

def find_pdf_files(root_dir: str) -> list[str]:
    pdf_files = []

    for current_dir, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files.append(
                    os.path.join(current_dir, filename)
                )

    return sorted(pdf_files)


# ============================================================
# CLEAR THE CONTENTS OF THE MOUNTED CHROMA VOLUME
# ============================================================

def clear_chroma_contents():
    """
    Delete everything INSIDE the mounted Chroma directory.

    IMPORTANT:
    We must NOT delete CHROMA_DIR itself because Railway mounts
    the persistent Volume at that exact path.
    """

    os.makedirs(CHROMA_DIR, exist_ok=True)

    print(
        "Removing previous/partial Chroma database contents..."
    )

    for name in os.listdir(CHROMA_DIR):

        path = os.path.join(
            CHROMA_DIR,
            name
        )

        try:

            if os.path.isdir(path) and not os.path.islink(path):

                shutil.rmtree(path)

            else:

                os.remove(path)

        except FileNotFoundError:
            # Another cleanup operation may already have removed it.
            pass


# ============================================================
# CREATE VECTOR STORE
# ============================================================

def create_vector_store():

    print(
        "Loading sentence-transformers embeddings "
        "(all-MiniLM-L6-v2)..."
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",

        model_kwargs={
            "device": "cpu"
        },

        encode_kwargs={
            "batch_size": EMBED_BATCH_SIZE,
            "normalize_embeddings": True,
        },
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_metadata={
            "hnsw:space": "cosine"
        },
    )

    return vector_store


# ============================================================
# INGESTION
# ============================================================

def ingest():

    if not os.path.isdir(DOCS_DIR):

        raise FileNotFoundError(
            f"Create this folder and add PDFs: {DOCS_DIR}"
        )


    # --------------------------------------------------------
    # FIND PDFs
    # --------------------------------------------------------

    print(
        f"Loading PDFs from {DOCS_DIR} "
        "(including subfolders)..."
    )

    pdf_files = find_pdf_files(DOCS_DIR)

    print(
        f"   Found {len(pdf_files)} PDF files."
    )

    if not pdf_files:

        raise RuntimeError(
            "No PDFs found under backend/guideline_docs."
        )


    # --------------------------------------------------------
    # IMPORTANT:
    # KEEP THE RAILWAY MOUNT DIRECTORY.
    # CLEAR ONLY ITS CONTENTS.
    # --------------------------------------------------------

    clear_chroma_contents()


    # --------------------------------------------------------
    # CREATE EMBEDDING MODEL + CHROMA
    # --------------------------------------------------------

    vector_store = create_vector_store()


    # --------------------------------------------------------
    # TEXT SPLITTER
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    pending_chunks = []

    total_pages = 0
    total_chunks = 0
    total_added = 0

    failed_files = []

    start_time = time.time()


    print()
    print(
        "Beginning memory-efficient ingestion..."
    )


    # ========================================================
    # PROCESS ONE PDF AT A TIME
    # ========================================================

    for pdf_index, pdf_path in enumerate(
        pdf_files,
        start=1
    ):

        rel_path = os.path.relpath(
            pdf_path,
            DOCS_DIR
        )

        print(
            f"[{pdf_index}/{len(pdf_files)}] "
            f"loading {rel_path}"
        )


        try:

            loader = PyPDFLoader(
                pdf_path
            )


            # ------------------------------------------------
            # lazy_load():
            # only one page is loaded into memory at a time.
            # ------------------------------------------------

            for page_doc in loader.lazy_load():

                total_pages += 1


                # --------------------------------------------
                # Split this page into chunks.
                # --------------------------------------------

                page_chunks = splitter.split_documents(
                    [page_doc]
                )

                pending_chunks.extend(
                    page_chunks
                )

                total_chunks += len(
                    page_chunks
                )


                # --------------------------------------------
                # Write small batches to Chroma.
                # --------------------------------------------

                while len(pending_chunks) >= ADD_BATCH_SIZE:

                    batch = pending_chunks[
                        :ADD_BATCH_SIZE
                    ]

                    pending_chunks = pending_chunks[
                        ADD_BATCH_SIZE:
                    ]


                    vector_store.add_documents(
                        batch
                    )


                    total_added += len(
                        batch
                    )


                    elapsed = (
                        time.time() - start_time
                    )

                    print(
                        f"   Added {total_added} chunks | "
                        f"pages {total_pages} | "
                        f"elapsed {elapsed / 60:.1f} min"
                    )


                    # Explicitly release the batch.
                    del batch

                    gc.collect()


                # --------------------------------------------
                # Release page objects immediately.
                # --------------------------------------------

                del page_chunks
                del page_doc

                gc.collect()


            # Release PDF loader.
            del loader

            gc.collect()


        except Exception as exc:

            failed_files.append(
                (
                    rel_path,
                    str(exc)
                )
            )

            print(
                f"   WARNING: skipped "
                f"{rel_path}: {exc}"
            )


    # ========================================================
    # WRITE FINAL SMALL BATCH
    # ========================================================

    if pending_chunks:

        vector_store.add_documents(
            pending_chunks
        )

        total_added += len(
            pending_chunks
        )

        pending_chunks.clear()

        gc.collect()


    # ========================================================
    # REPORT FAILED FILES
    # ========================================================

    if failed_files:

        print()
        print(
            f"WARNING: {len(failed_files)} "
            f"PDF files failed."
        )

        for rel_path, error in failed_files:

            print(
                f"   FAILED: {rel_path}"
            )

            print(
                f"      {error}"
            )


    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if total_added == 0:

        raise RuntimeError(
            "No chunks were written to Chroma. "
            "The ingestion is not complete."
        )


    # ========================================================
    # INGESTION SUCCESS
    # ========================================================

    elapsed_minutes = (
        time.time() - start_time
    ) / 60


    print()
    print(
        "=============================================="
    )

    print(
        "INGESTION COMPLETE"
    )

    print(
        "=============================================="
    )

    print(
        f"Pages processed: {total_pages}"
    )

    print(
        f"Chunks created:  {total_chunks}"
    )

    print(
        f"Chunks stored:   {total_added}"
    )

    print(
        f"Failed PDFs:     {len(failed_files)}"
    )

    print(
        f"Time:            {elapsed_minutes:.1f} minutes"
    )

    print(
        f"Chroma path:     {CHROMA_DIR}"
    )

    print(
        "=============================================="
    )


    # ========================================================
    # COMPLETION MARKER
    #
    # This is created ONLY after successful ingestion.
    # ========================================================

    with open(
        COMPLETE_MARKER,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "AccuCare guideline ingestion completed successfully.\n"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    ingest()