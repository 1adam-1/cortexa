from entities.models import Chunk
import faiss


def retrieve_top_chunks(question, chunks : list[Chunk], index, embedding_model, k=40):
    k = min(k, len(chunks))
    if k == 0:
        return []

    # Create a mapping of {id: chunk_object} since Faiss returns IDs, not list indices
    chunk_map = {chunk.id: chunk for chunk in chunks}

    question_embedded = embedding_model.encode(
        ["Represent this sentence for searching relevant passages: " + question]
    ).astype("float32")
    faiss.normalize_L2(question_embedded)
    scores, indices = index.search(question_embedded, k)

    top_chunks = []
    for i in range(k):
        idx = int(indices[0][i])
        if idx == -1:
            continue
        
        # Look up the chunk in our map using the ID returned by Faiss
        chunk = chunk_map.get(idx)
        if chunk:
            top_chunks.append(chunk)

    return top_chunks


def rerank_chunks(question, chunks : list[Chunk], reranker, top_n=8):
    if not chunks:
        return []

    pairs = [(question, chunk.content) for chunk in chunks]
    scores = reranker.predict(pairs, batch_size=16)

    for chunk, score in zip(chunks, scores):
        chunk.rerank_score = float(score)

    chunks = sorted(chunks, key=lambda x: getattr(x, 'rerank_score', 0), reverse=True)
    return chunks[:top_n]
