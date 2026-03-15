import numpy as np
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer


def load_embedding_models():
    embedding_model = SentenceTransformer(
        "BAAI/bge-base-en-v1.5",
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    reranker = CrossEncoder("BAAI/bge-reranker-base")
    return embedding_model, reranker


def compute_embeddings(chunks, embedding_model):
    text = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(text)
    return np.array(embeddings).astype("float32")
