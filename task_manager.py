from db_setup import get_chroma_collection
from embeddings import embed_texts
import time
import uuid
import re

# Priority codes
PRIORITIES = {
    "ferrari": "urgent and important",
    "tesla": "semi-urgent and important",
    "amazon": "not urgent but important",
    "suzuki": "urgent, not important but necessary",
    "orange": "semi-urgent, not important but eventually necessary",
    "budweiser": "not important not urgent",
    "greyhound": "semi-complete needs follow up"
}

def add_task(task_text: str, priority_code: str = None):
    """Add a task to the vector database with priority metadata"""
    collection = get_chroma_collection()
    
    # Extract priority if mentioned in text
    if not priority_code:
        for code in PRIORITIES:
            if code.lower() in task_text.lower():
                priority_code = code
                break
    
    # Create metadata
    metadata = {
        "type": "task",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed": False
    }
    
    if priority_code and priority_code.lower() in PRIORITIES:
        metadata["priority_code"] = priority_code.lower()
        metadata["priority_description"] = PRIORITIES[priority_code.lower()]
    
    # Generate unique ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # Embed and store
    embedding = embed_texts([task_text])[0]
    collection.add(
        documents=[task_text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[task_id]
    )
    
    return task_id, metadata

def complete_task(task_id: str):
    """Mark a task as completed"""
    collection = get_chroma_collection()
    
    # Get current metadata
    result = collection.get(ids=[task_id])
    if not result or not result["ids"]:
        return False, "Task not found"
    
    # Update metadata
    metadata = result["metadatas"][0]
    metadata["completed"] = True
    metadata["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # We need to re-add the document to update metadata
    collection.update(
        ids=[task_id],
        metadatas=[metadata]
    )
    
    return True, "Task marked as completed"

def query_tasks(query: str, top_k=5, filter_metadata=None):
    """Search for tasks by semantic similarity and/or metadata filters"""
    collection = get_chroma_collection()
    query_embedding = embed_texts([query])[0]
    
    # Handle priority code filtering in query
    if not filter_metadata:
        filter_metadata = {}
        for code in PRIORITIES:
            if code.lower() in query.lower():
                filter_metadata["priority_code"] = code.lower()
                break
    
    # Construct the query
    #where = {}
    if filter_metadata:
        where = filter_metadata
    
    # Execute query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        #where=where
    )
    
    return results

def add_reflection(reflection_text: str, mood_score: int = None):
    """Add a reflection/mood entry to the vector database"""
    collection = get_chroma_collection()
    
    # Try to extract mood score from text if not provided
    if mood_score is None:
        # Simple heuristic - check for numerical values
        numbers = re.findall(r'\b([0-9]|10)\b', reflection_text)
        if numbers and 0 <= int(numbers[0]) <= 10:
            mood_score = int(numbers[0])
    
    # Create metadata
    metadata = {
        "type": "reflection",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": time.strftime("%Y-%m-%d")
    }
    
    if mood_score is not None:
        metadata["mood_score"] = mood_score
    
    # Generate unique ID
    reflection_id = f"reflection_{uuid.uuid4().hex[:8]}"
    
    # Embed and store
    embedding = embed_texts([reflection_text])[0]
    collection.add(
        documents=[reflection_text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[reflection_id]
    )
    
    return reflection_id, metadata