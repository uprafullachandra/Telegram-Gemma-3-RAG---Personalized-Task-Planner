'''import chromadb
from chromadb.config import Settings

def get_chroma_collection(collection_name="personal_assistant"):
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_store"  # folder to store vector database
    ))
    return client.get_or_create_collection(name=collection_name)

# Quick test to verify
if __name__ == "__main__":
    collection = get_chroma_collection()
    print("Chroma collection created:", collection.name)'''

from chromadb import PersistentClient

def get_chroma_collection(collection_name="personal_assistant"):
    client = PersistentClient(path="./chroma_store")
    return client.get_or_create_collection(name=collection_name)

# Quick test to verify
if __name__ == "__main__":
    collection = get_chroma_collection()
    print("Chroma collection created:", collection.name)
