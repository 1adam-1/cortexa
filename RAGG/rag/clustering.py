import json
import uuid
import numpy as np
import hdbscan
import faiss
from sklearn.preprocessing import normalize

MODEL_LIMIT = 8192
MAX_OUTPUT = 300
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN

SYSTEM_PROMPT = """You are a knowledge extraction engine.
Given a set of text chunks from a document cluster, extract the key concepts.
Respond ONLY with valid JSON. No preamble, no markdown fences.

Schema:
{
  "concepts": [
    {
      "name": "string",
      "definition": "string (2-3 sentences)",
      "keywords": ["string"],
      "importance": 0.0-1.0,
      "source_chunks": [int]
    }
  ],
  "cluster_summary": "string (1-2 sentences)"
}"""


def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def cluster_chunks(chunks, embeddings, min_cluster_size=5, min_samples=3):
    normed = normalize(embeddings, norm="l2")
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = model.fit_predict(normed)

    clusters = {}
    noise = []
    for chunk, label, emb in zip(chunks, labels, embeddings):
        entry = {**chunk, "embedding": emb}
        if label == -1:
            noise.append(entry)
        else:
            clusters.setdefault(label, []).append(entry)

    return clusters, noise


def build_cluster_context(cluster, tokenizer):
    parts = []
    total_tokens = 0

    for i,chunk in enumerate(cluster):
        text = f"[chunk{i}] \n title: {chunk.get('title', '')} \n {chunk['text']} \n"
        if total_tokens + count_tokens(text, tokenizer) > DEFAULT_BUDGET_INPUT:
            break
        parts.append(text)
        total_tokens += count_tokens(text, tokenizer)
    
    return "\n\n".join(parts)


def extract_concept_from_clusters(cluster, model, tokenizer, cluster_id="unknown"):
    context = build_cluster_context(cluster, tokenizer)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Cluster {cluster_id} — extract concepts from these chunks:

{context}

Respond ONLY with valid JSON. No explanation, no markdown."""
        }
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=MAX_OUTPUT,
        do_sample=False,
        temperature=None,
        top_p=None,
    )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)








