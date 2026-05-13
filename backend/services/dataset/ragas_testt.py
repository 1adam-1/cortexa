import os
import json
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

def evaluate_rag_pipeline(predictions_file_path):
    """
    Évalue les performances du RAG en utilisant la bibliothèque Ragas.
    
    predictions_file_path doit pointer vers un fichier JSON contenant une liste d'objets avec:
    - "question" (str) : La question posée.
    - "answer" (str) : La réponse générée par votre RAG.
    - "contexts" (list[str]) : Les passages récupérés par votre retriever.
    - "ground_truth" (str) : (Optionnel) La bonne réponse attendue.
    """
    if not os.path.exists(predictions_file_path):
        raise FileNotFoundError(f"Le fichier {predictions_file_path} n'existe pas.")

    with open(predictions_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Création du Dataset HuggingFace à partir des données
    df = pd.DataFrame(data)
    dataset = Dataset.from_pandas(df)

    # Définition des métriques à calculer
    metrics = [
        faithfulness,       # Fait-il des hallucinations par rapport au contexte?
        answer_relevancy,   # La réponse est-elle pertinente par rapport à la question?
        context_precision,  # Les contextes récupérés sont-ils vraiment pertinents?
        context_recall,     # Le contexte contient-il toutes les infos pour la réponse?
    ]

    print("Début de l'évaluation Ragas... (Cela peut prendre un certain temps)")
    
    # Configuration du LLM Ollama pour l'évaluation locale
    ollama_llm = ChatOllama(model="mistral-nemo", format="json", temperature=0.0) 
    ragas_llm = LangchainLLMWrapper(ollama_llm)
    
    # Configuration du modèle d'embedding HuggingFace identique à dataset_generation.py
    from langchain_huggingface import HuggingFaceEmbeddings
    hf_emb = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(hf_emb)
    
    # Configuration pour Ragas (désactiver la parallélisation et augmenter le timeout)
    from ragas.run_config import RunConfig
    run_config = RunConfig(timeout=180, max_workers=1)
    
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=run_config,
    )
    
    df_results = result.to_pandas()
    
    results_path = predictions_file_path.replace(".json", "_ragas_results.csv")
    df_results.to_csv(results_path, index=False, encoding="utf-8")
    print(f"Évaluation terminée ! Résultats sauvegardés dans : {results_path}")
    
    return result

# Exemple d'exécution
if __name__ == "__main__":
    # Chemin absolu pour éviter les problèmes de dossier de travail (cwd)
    current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/services/dataset
    predictions_path = os.path.join(current_dir, "../../evaluation/predictions.json")
    
    evaluate_rag_pipeline(predictions_path)
