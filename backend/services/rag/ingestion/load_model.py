from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

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
        device_map="cuda",
    )
    return tokenizer, generation_model

def load_embedding_models():
    embedding_model = SentenceTransformer(
        "BAAI/bge-m3",
        device="cpu",
    )
    reranker = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
    return embedding_model, reranker