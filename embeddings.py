import torch
from sentence_transformers import SentenceTransformer

# Choose a smaller model for efficiency
model_name = "sentence-transformers/all-MiniLM-L6-v2"

# Adjust device based on your system configuration
device = "cuda:0" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer(model_name, device=device)

def embed_texts(texts: list[str]) -> list[list[float]]:
    return embedding_model.encode(texts, show_progress_bar=False).tolist()