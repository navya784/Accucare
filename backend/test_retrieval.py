"""
Debug script: tests raw retrieval only (no LLM call) to see exactly which
document chunks match a given question, with similarity scores.

USAGE (run from project root, venv activated):

    python backend\\test_retrieval.py "your question here"

Examples:
    python backend\\test_retrieval.py "What is the first-line treatment for STEMI?"
    python backend\\test_retrieval.py "management of stable angina"
    python backend\\test_retrieval.py "sepsis recognition and early management"

If you run it with no question, it falls back to a few default test
questions so it still does something useful.
"""
import sys
from backend.app.services.rag_engine import vector_store

DEFAULT_QUERIES = [
    "What is the first-line treatment for STEMI?",
    "acute coronary syndrome treatment",
]


def run_query(query: str, k: int = 6):
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print('='*80)

    results = vector_store.similarity_search_with_score(query, k=k)

    if not results:
        print("  No results returned at all.")
        return

    for i, (doc, score) in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        filename = source.split("\\")[-1].split("/")[-1]
        snippet = doc.page_content[:120].replace("\n", " ")
        print(f"  [{i}] score={score:.4f}  file={filename}")
        print(f"       snippet: {snippet}...")


if __name__ == "__main__":
    # everything after the script name, joined back into one question,
    # so you can type a normal question without quoting every word
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_query(query)
    else:
        print("No question given — running default test set instead.")
        print("Tip: python backend\\test_retrieval.py \"your question here\"\n")
        for q in DEFAULT_QUERIES:
            run_query(q)