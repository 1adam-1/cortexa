from entities.models import Chunk, Concept
import faiss


def retrieve_top_chunks(question, chunks : list[Chunk], index, embedding_model, k=40, threshold=0.3):
    k = min(k, len(chunks))
    if k == 0:
        return []

    chunk_map = {chunk.id: chunk for chunk in chunks}

    question_embedded = embedding_model.encode(["Represent this sentence for searching relevant passages: " + question]).astype("float32")
    faiss.normalize_L2(question_embedded)
    scores, indices = index.search(question_embedded, k)

    top_chunks = []
    for i in range(k):
        score = float(scores[0][i])
        idx = int(indices[0][i])
        
        # Filtrer avec le threshold (seuil de similarité)
        if score < threshold or idx == -1:
            continue
        
        # Look up the chunk in our map using the ID returned by Faiss
        chunk = chunk_map.get(idx)
        if chunk:
            chunk.faiss_score = score
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

def rerank_unified(question, items, reranker, top_n=8):
    if not items:
        return []

    pairs = []
    for item in items:
        if hasattr(item, "content"):
            text_to_rerank = item.content
        elif hasattr(item, "definition"):
            text_to_rerank = f"{item.name}: {item.definition}"
        else:
            text_to_rerank = ""
        pairs.append((question, text_to_rerank))

    scores = reranker.predict(pairs, batch_size=16)

    for item, score in zip(items, scores):
        item.rerank_score = float(score)

    items = sorted(items, key=lambda x: getattr(x, 'rerank_score', 0), reverse=True)
    filtered = [item for item in items[:top_n] if item.rerank_score > 0.0]
    return filtered if len(filtered) >= 2 else items[:2]





