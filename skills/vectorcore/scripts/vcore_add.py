# vcore_add.py (serverless)
import argparse
import chromadb

def main():
    parser = argparse.ArgumentParser(description="Add entry to Serverless VectorCore Memory")
    parser.add_argument("--text", required=True, help="Text to add to memory.")
    parser.add_argument("--path", default="~/vectorcore/db", help="Path to persistent DB.")
    parser.add_argument("--collection", default="solomon_core_v1", help="Collection name.")
    args = parser.parse_args()

    try:
        client = chromadb.PersistentClient(path=args.path)
        collection = client.get_or_create_collection(name=args.collection)
        
        doc_id = str(collection.count())
        
        collection.add(documents=[args.text], ids=[doc_id])
        print(f"Successfully added memory with ID {doc_id} to collection '{args.collection}'.")
    except Exception as e:
        print(f"Error updating Serverless VectorCore DB: {e}")

if __name__ == "__main__":
    main()
