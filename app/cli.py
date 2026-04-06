import os
import random

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from generation.qa import build_context, generate_answer
from generation.qcm import generate_qcm
from generation.questions import ask_question
from generation.summary import generate_summary
from rag.chunking import chunk_text_by_tokens
from rag.embeddings import compute_embeddings, load_embedding_models
from rag.ingestion import extract_elements
from rag.retrieval import rerank_chunks, retrieve_top_chunks
from storage.index import (
    create_faiss_index,
    load_chunks,
    load_index,
    save_chunks,
    save_index,
)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def load_generation_model(model_id="meta-llama/Meta-Llama-3.1-8B-Instruct"):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    generation_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
    )
    return tokenizer, generation_model


def menu():
    print("1. Ask a question")
    print("2. Generate summary")
    print("3. Generate QCM")
    print("4. Generate open-ended questions")
    print("5. Exit")
    choice = input("Choose an option: ")
    return choice.strip()


def main():
    path = "ml.pdf"
    index_path = "index.faiss"
    chunks_path = "chunks.pkl"

    tokenizer, generation_model = load_generation_model()
    embedding_model, reranker = load_embedding_models()

    if os.path.exists(index_path) and os.path.exists(chunks_path):
        index = load_index(index_path)
        chunks = load_chunks(chunks_path)
    else:
        if os.path.exists(index_path) and not os.path.exists(chunks_path):
            print("index.faiss found but chunks.pkl missing, rebuilding index and chunks...")
        elif os.path.exists(chunks_path) and not os.path.exists(index_path):
            print("chunks.pkl found but index.faiss missing, rebuilding index...")

        sections = extract_elements(path)
        chunks = chunk_text_by_tokens(sections, tokenizer, max_tokens=500, min_tokens=50, overlap=50)
        chunk_embeddings = compute_embeddings([c for c in chunks], embedding_model)
        index = create_faiss_index(chunk_embeddings)
        save_index(index, index_path)
        save_chunks(chunks, chunks_path)

    while True:
        print("\n\n ***********MENU***********\n\n")
        
        choice = menu()
        if choice == "1":
            question = input("Entre ta question: ").strip()
            candidates = retrieve_top_chunks(question, chunks, index, embedding_model)
            top_chunks = rerank_chunks(question, candidates, reranker)
            context = build_context(top_chunks, tokenizer, question)
            answer = generate_answer(context, question, tokenizer, generation_model)
            print("Question :", question)
            print("Réponse :", answer)

        elif choice == "2":
            random_chunks = random.sample(chunks, min(len(chunks), 5))
            summary_prompt = f"""
                            Résume le contenu suivant pour un étudiant.

                            Concentre-toi sur :
                            - concepts clés
                            - définitions importantes
                            - idées principales

                            Contexte :
                            """
            context = build_context(chunks=random_chunks, tokenizer=tokenizer, question="", prompt=summary_prompt)
            summary = generate_summary(tokenizer, generation_model, context)
            print("Summary :\n", summary)

        elif choice == "3":
            random_chunks = random.sample(chunks, min(len(chunks), 8))
            qcm_prompt = f"""
            Genere 5 questions a choix multiples a partir du contexte suivant.

            Contexte:
            """
            context = build_context(chunks=random_chunks, tokenizer=tokenizer, question="", prompt=qcm_prompt)
            qcm = generate_qcm(context, tokenizer, generation_model)
            print("QCM :\n", qcm)

        elif choice == "4":
            random_chunks = random.sample(chunks, min(len(chunks), 5))
            open_questions_prompt = f"""
            Genere 3 questions ouvertes qui evaluent la comprehension.
            Contexte:
            """
            context = build_context(chunks=random_chunks, tokenizer=tokenizer, question="", prompt=open_questions_prompt)
            questions = ask_question(context, tokenizer, generation_model)
            print("Questions :\n", questions)

        elif choice == "5":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")
            continue


if __name__ == "__main__":
    main()
