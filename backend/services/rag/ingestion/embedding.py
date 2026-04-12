import numpy as np
import pickle

import faiss
from entities.models import Chunk_embedding, db


def compute_embeddings(chunks, embedding_model):
    text = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(text)
    return np.array(embeddings).astype("float32")



def create_faiss_index(chunks, embeddings):
    dimension = embeddings.shape[1]

    base_index = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIDMap(base_index)

    faiss.normalize_L2(embeddings)
    ids = np.array([chunk["id"] for chunk in chunks]).astype("int64")

    index.add_with_ids(embeddings, ids)
    for chunk_id in ids:
        chunk_embedding = Chunk_embedding(
            id_chunk=chunk_id,
            id_faiss=chunk_id,
            dimension=dimension,
        )
        db.session.add(chunk_embedding)
    db.session.commit()

    return index

   
def save_chunks(chunks, chunks_path):
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)


def load_chunks(chunks_path):
    with open(chunks_path, "rb") as f:
        return pickle.load(f)


def save_index(index, index_path):
    faiss.write_index(index, index_path)


def load_index(index_path):
    return faiss.read_index(index_path)
