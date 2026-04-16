from entities.models import Chunk
from threading import Thread 
from transformers import TextIteratorStreamer

MODEL_LIMIT = 8192
MAX_OUTPUT = 1024
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN

SYSTEM_PROMPT = """You are a strict RAG assistant specialized in document analysis.
CRITICAL RULES:
1. ABSOLUTE LANGUAGE RULE: You MUST detect the language of the user's question (e.g., Arabic, English, French) and MUST reply EXCLUSIVELY in that EXACT SAME language. If the question is in Arabic, you MUST answer in Arabic.
2. Analyze the question to identify the user's intent.
3. IF THE QUESTION IS A GREETING (e.g., Hello, Hi, Bonjour, Salam):
   * Reply pleasantly in the SAME language and ask how you can help with their documents.
   * Ignore strict structure rules and context for these cases.
4. IF THE QUESTION IS ABOUT DOCUMENTS (RAG):
   * Prioritize the provided context to answer.
   * Only answer if the information is present or clearly deductible from the context.
   * If information is insufficient, state it clearly in the same language as the question.
5. Highlight key concepts in **bold**.
6. Never invent information. Do not use external knowledge for document questions.
"""

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def build_context(chunks : list[Chunk], tokenizer, question , budget_input=DEFAULT_BUDGET_INPUT):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"""QUESTION:
        {question}

        CONTEXT:

        ANSWER:"""
        }
    ]
    
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    total_tokens = count_tokens(prompt, tokenizer)
    context_parts = []

    for i, c in enumerate(chunks, start=1):
        chunk_block = f"Extrait {i}:\n{c.content}"
        chunk_tokens = count_tokens(chunk_block, tokenizer)

        if total_tokens + chunk_tokens <= budget_input:
            context_parts.append(chunk_block)
            total_tokens += chunk_tokens
        else:
            break

    return "\n\n".join(context_parts)


def generate_answer(context, question, tokenizer, generation_model, max_new_tokens=MAX_OUTPUT):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"""QUESTION:
        {question}

        CONTEXT:
        {context}

        ANSWER:"""
        }
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)

    # 1. Initialize the streamer
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    # 2. Run generation in a separate thread because .generate() is blocking
    generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=max_new_tokens, do_sample=False)
    thread = Thread(target=generation_model.generate, kwargs=generation_kwargs)
    thread.start()
    # 3. Yield chunks as they arrive
    for new_text in streamer:
        yield new_text
