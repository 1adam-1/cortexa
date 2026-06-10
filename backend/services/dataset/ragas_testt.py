import os
import json
import sys
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_ollama import ChatOllama
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.run_config import RunConfig
from dotenv import load_dotenv


def evaluate_rag_pipeline(predictions_file_path: str | None = None) -> object:
    """
    Évalue le pipeline RAG avec RAGAS.

    Format attendu dans predictions.json :
    {
      "samples": [
        {
          "user_input": "...",
          "reference": "...",
          "reference_contexts": ["...", "..."],
          "retrieved_contexts": ["...", "..."],
          "response": "..."
        },
        ...
      ]
    }
    """

    # ── Chemins ──────────────────────────────────────────────────────────────
    if predictions_file_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        predictions_file_path = os.path.abspath(
            os.path.join(current_dir, "../../evaluation/predictions.json")
        )

    if not os.path.exists(predictions_file_path):
        raise FileNotFoundError(
            f"Fichier introuvable : {predictions_file_path}\n"
            "Lance d'abord generate_predictions.py"
        )

    # ── Chargement des données ────────────────────────────────────────────────
    with open(predictions_file_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Le JSON peut être {"samples": [...]} ou directement [...]
    samples = raw["samples"] if isinstance(raw, dict) and "samples" in raw else raw

    if not samples:
        raise ValueError("Aucun sample trouvé dans le fichier de prédictions.")

    # ── Validation et nettoyage des samples ───────────────────────────────────
    required_fields = {"user_input", "reference", "reference_contexts", "retrieved_contexts", "response"}
    clean_samples = []
    skipped = 0

    for i, s in enumerate(samples):
        missing = required_fields - set(s.keys())
        if missing:
            print(f"  [WARN] Sample {i} ignoré — champs manquants : {missing}")
            skipped += 1
            continue

        if not s.get("retrieved_contexts"):
            print(f"  [WARN] Sample {i} ignoré — retrieved_contexts vide")
            skipped += 1
            continue

        if not s.get("reference_contexts"):
            print(f"  [WARN] Sample {i} ignoré — reference_contexts vide")
            skipped += 1
            continue

        clean_samples.append({
            "user_input":         s["user_input"],
            "reference":          s["reference"],
            "reference_contexts": s["reference_contexts"],
            "retrieved_contexts": s["retrieved_contexts"],
            "response":           s["response"],
        })

    print(f"Samples valides : {len(clean_samples)} / {len(samples)} ({skipped} ignorés)")

    if not clean_samples:
        raise ValueError("Aucun sample valide après nettoyage. Vérifie ton predictions.json.")

    dataset = Dataset.from_list(clean_samples)

    # ── LLM : Ollama mistral-nemo local ──────────────────────────────────────
    ollama_llm = ChatOllama(
        model="mistral-nemo",
        format="json",
        temperature=0.0,
    )
    ragas_llm = LangchainLLMWrapper(ollama_llm)

    # ── Embeddings : BGE-M3 ───────────────────────────────────────────────────
    print("Chargement du modèle d'embedding BGE-M3...")
    hf_emb = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(hf_emb)

    # ── Métriques RAGAS ───────────────────────────────────────────────────────
    metrics = [
        faithfulness,       # Hallucinations par rapport au contexte récupéré ?
        answer_relevancy,   # La réponse est-elle pertinente à la question ?
        context_precision,  # Les chunks récupérés sont-ils vraiment utiles ?
        context_recall,     # Le contexte couvre-t-il la réponse de référence ?
    ]

    # ── Évaluation ────────────────────────────────────────────────────────────
    run_config = RunConfig(
        timeout=180,
        max_workers=1,  # Obligatoire avec Ollama local pour éviter la saturation RAM
    )

    print(f"\nDébut évaluation RAGAS sur {len(clean_samples)} samples...")
    print("Attention : avec Ollama local, cette étape peut prendre plusieurs heures.\n")

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=run_config,
    )

    # ── Sauvegarde des résultats ──────────────────────────────────────────────
    df_results = result.to_pandas()

    results_path = predictions_file_path.replace(".json", "_ragas_results.csv")
    df_results.to_csv(results_path, index=False, encoding="utf-8")

    # Résumé dans le terminal
    print("\n" + "=" * 50)
    print("RÉSULTATS RAGAS")
    print("=" * 50)
    for metric in metrics:
        score = df_results[metric.name].mean()
        print(f"  {metric.name:<25} : {score:.4f}")
    print("=" * 50)
    print(f"\nRésultats détaillés sauvegardés : {results_path}")

    return result


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    _dotenv_path = os.path.abspath(os.path.join(_backend_path, "..", ".env"))
    load_dotenv(dotenv_path=_dotenv_path)

    evaluate_rag_pipeline()