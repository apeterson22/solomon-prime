# vcore_search.py (serverless)
import argparse
import chromadb

def main():
    parser = argparse.ArgumentParser(description="Search Serverless VectorCore Memory")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument("--path", default="~/vectorcore/db", help="Path to persistent DB.")
    parser.add_argument("--collection", default="solomon_core_v1", help="Collection name.")
    parser.add_argument("--results", default=3, type=int, help="Number of results to return.")
    args = parser.parse_args()

    try:
        client = chromadb.PersistentClient(path=args.path)
        collection = client.get_collection(name=args.collection)
        
        results = collection.query(query_texts=[args.query], n_results=args.results)
        
        print("--- VectorCore Search Results ---")
        if results and results['documents']:
            for doc in results['documents'][0]:
                print(f"- {doc}")
        else:
            print("No relevant memories found.")
        print("-------------------------------")

    except Exception as e:
        print(f"Error searching Serverless VectorCore DB: {e}")

if __name__ == "__main__":
    main()
