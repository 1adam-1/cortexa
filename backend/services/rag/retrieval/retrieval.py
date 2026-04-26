from entities.models import Chunk, Concept
import faiss


def retrieve_top_chunks(question, chunks : list[Chunk], index, embedding_model, k=40):
    k = min(k, len(chunks))
    if k == 0:
        return []

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
    return items[:top_n]


def retrieve_top_concepts(query, concepts : list[Concept], index, embedding_model, k=20):
    k = min(k, len(concepts))
    if k == 0:
        return []

    concept_map = {concept.id: concept for concept in concepts}
    query_embedded = embedding_model.encode(
        ["Represent this sentence for searching relevant concepts: " + query]
    ).astype("float32")

    faiss.normalize_L2(query_embedded)
    scores, indices = index.search(query_embedded, k)

    top_concepts=[]
    for i in range(k):
        idx=int(indices[0][i])
        if idx == -1:
            continue

        concept=concept_map.get(idx)
        if concept:
            top_concepts.append(concept)
    
    return top_concepts

def rerank_concepts(query, concepts : list[Concept], reranker, top_n=4):
    pairs= [(query, concept.definition) for concept in concepts]
    scores = reranker.predict(pairs, batch_size=16)

    for concept, score in zip(concepts, scores):
        concept.rerank_score = float(score)
    
    concepts = sorted(concepts, key=lambda x: getattr(x, 'rerank_score', 0), reverse=True)
    return concepts[:top_n]



