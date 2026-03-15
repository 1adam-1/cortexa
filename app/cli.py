import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from generation.qa import build_context, generate_answer
from generation.qcm import generate_qcm
from generation.questions import ask_question
from generation.summary import generate_summary
from rag.embeddings import compute_embeddings, load_embedding_models
from rag.ingestion import chunk_pages, extract_pages_from_pdf
from rag.retrieval import rerank_chunks, retrieve_top_chunks
from storage.index import (
    create_faiss_index,
    load_chunks,
    load_index,
    save_chunks,
    save_index,
)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def load_generation_model(model_id="mistralai/Mistral-7B-Instruct-v0.2"):
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

        pages = extract_pages_from_pdf(path)
        chunks = chunk_pages(pages, tokenizer)
        chunk_embeddings = compute_embeddings(chunks, embedding_model)
        index = create_faiss_index(chunk_embeddings)
        save_index(index, index_path)
        save_chunks(chunks, chunks_path)

    while True:
        choice = menu()

        if choice == "1":
            question = input("Entre ta question: ").strip()
            candidates = retrieve_top_chunks(question, chunks, index, embedding_model)
            top_chunks = rerank_chunks(question, candidates, reranker)
            context = build_context(top_chunks, question, tokenizer)
            answer = generate_answer(context, question, tokenizer, generation_model)
            print("Question :", question)
            print("Answer :", answer)

        elif choice == "2":
            summary = generate_summary(chunks, tokenizer, generation_model)
            print("Summary :\n", summary)

        elif choice == "3":
            context = build_context(chunks[:8], "Genere un QCM", tokenizer)
            qcm = generate_qcm(context, tokenizer, generation_model)
            print("QCM :\n", qcm)

        elif choice == "4":
            context = build_context(chunks[:8], "Genere des questions ouvertes", tokenizer)
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
