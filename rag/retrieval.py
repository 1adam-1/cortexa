import faiss


def retrieve_top_chunks(question, chunks, index, embedding_model, k=40):
    k = min(k, len(chunks))
    if k == 0:
        return []

    question_embedded = embedding_model.encode(
        ["Represent this sentence for searching relevant passages: " + question]
    ).astype("float32")
    faiss.normalize_L2(question_embedded)
    scores, indices = index.search(question_embedded, k)

    top_chunks = []
    for i in range(k):
        if indices[0][i] == -1:
            continue
        chunk = chunks[indices[0][i]]
        score = scores[0][i]
        top_chunks.append(
            {   "title": chunk["title"],
                "text": chunk["text"],
                "score": score,
            }
        )
    return top_chunks


def rerank_chunks(question, chunks, reranker, top_n=8):
    if not chunks:
        return []

    pairs = [(question, chunk["text"]) for chunk in chunks]
    scores = reranker.predict(pairs, batch_size=16)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = score

    chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return chunks[:top_n]
