import pickle

import faiss


def create_faiss_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
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
