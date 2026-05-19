import re 
import json
from sentence_transformers  import CrossEncoder
from entities.models import Evaluation, db
from scipy.special import softmax


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if len(s.split()) > 3]

def compute_faithfulness (answer:str, context, nli_model:CrossEncoder, threshold:float=0.5):
    sentences = split_sentences(answer)
    if not sentences:
        return {"faithfulness_score": 0.0, "entailed": 0, "total": 0, "details": []}
    
    contexts = []
    for item in context:
        if hasattr(item, "content"):
            contexts.append(item.content)
        if hasattr(item, "definition"):
            contexts.append(f"Name: {item.name}, Definition: {item.definition}")
    
    if not contexts:
        return {"faithfulness_score": 0.0, "entailed": 0, "total": len(sentences), "details": []}
    
    detailed_results = []
    entailed_count = 0

    for sentence in sentences:
        pairs=[[c, sentence] for c in contexts]
        scores = nli_model.predict(pairs)
        probs = softmax(scores, axis=1)
        entailment_probs = probs[:,2]
        max_prob = float(entailment_probs.max())
        best_chunk_idx = int(entailment_probs.argmax())
        is_entailed = max_prob >= threshold

        if is_entailed:
            entailed_count += 1

        detailed_results.append(
            {
               "sentence": sentence,
                "entailed": is_entailed,
                "best_score": round(max_prob, 4),
                 "best_chunk_idx": best_chunk_idx
            }
        )

    
    faithfulness_score = entailed_count / len(sentences)


    return {
        "faithfulness_score": round(faithfulness_score, 4),
        "entailed": entailed_count,
        "total": len(sentences),
        "details": detailed_results
    }


def compute_avg_rerank_score(context_items: list) -> float:
    scores = [
        getattr(item, "rerank_score", 0.0)
        for item in context_items
        if hasattr(item, "rerank_score")
    ]
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def evaluate_generation(id_generation, answer, context, nli_model):
    faithfulness_result = compute_faithfulness(
                answer, context, nli_model
            )
    avg_rerank_score = compute_avg_rerank_score(context)

    try:
        evaluation_details_json = json.dumps(
            faithfulness_result.get("details", []),
            ensure_ascii=False,
        )
    except TypeError:
        evaluation_details_json = json.dumps(
            [str(x) for x in faithfulness_result.get("details", [])],
            ensure_ascii=False,
        )

    try:
        new_evaluation = Evaluation(
          id_generation=id_generation,
          faithfulness=faithfulness_result["faithfulness_score"],
          entailed=faithfulness_result["entailed"],
            total_sentences=faithfulness_result["total"],
            avg_rerank_score=avg_rerank_score,
                        evaluation_details=evaluation_details_json,
      )

        db.session.add(new_evaluation)
        db.session.commit()
    
    except Exception as e:
            print(f"[Evaluation] Failed for generation {id_generation}: {e}")
            db.session.rollback()
