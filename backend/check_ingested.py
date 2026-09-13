import sys
from backend.app.services.rag_engine import vector_store


def check_file(partial_filename: str):
    collection = vector_store._collection

    # Pull metadata in batches instead of all at once - a single get() call
    # for 30k+ chunks exceeds SQLite's max SQL variable limit.
    batch_size = 1000
    offset = 0
    matches = []
    total_chunks = 0

    while True:
        batch = collection.get(include=["metadatas"], limit=batch_size, offset=offset)
        metadatas = batch["metadatas"]
        if not metadatas:
            break

        for metadata in metadatas:
            source = metadata.get("source", "")
            if partial_filename.lower() in source.lower():
                matches.append(source)

        total_chunks += len(metadatas)
        offset += batch_size
    print(f"\nTotal chunks in ChromaDB: {total_chunks}")
    print(f"Chunks matching '{partial_filename}': {len(matches)}")

    if matches:
        print(f"\n✅ Found! Example matching source path:\n   {matches[0]}")
        print(f"   Total chunks from this file: {len(matches)}")
    else:
        print(f"\n❌ NOT FOUND. No chunks in ChromaDB reference '{partial_filename}'.")
        print("   This means the file was never successfully ingested/embedded.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        check_file(query)
    else:
        print("Usage: python -m backend.check_ingested \"filename or partial name\"")