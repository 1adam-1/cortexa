from entities.models import Chunk
from threading import Thread 
from transformers import TextIteratorStreamer

MODEL_LIMIT = 8192
MAX_OUTPUT = 1024
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN

#Q/A prompt
SYSTEM_PROMPT_QA = """You are a strict RAG assistant specialized in document analysis.
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
   * Always cite the source extract and page number if it's available in the context (e.g., "[Source: Extrait 1, Page: 5]").
5. Highlight key concepts in **bold**.
6. Never invent information. Do not use external knowledge for document questions.
"""

# QCM prompt
def get_system_prompt_qcm(num_questions=5, difficulty="medium"):
    return f"""Generate {num_questions} relevant and precise multiple-choice questions with a '{difficulty}' difficulty level based on the provided context.
Each question must strictly include:
-4 answer options (A, B, C, D)
-1 single correct answer

CRITICAL JSON RULE : 
You MUST output ONLY valid JSON format. 
Do NOT include any introductory greetings, explanations, or conversational text.
Do NOT wrap the output in markdown code blocks like ```json ... ```. 
Start your response immediately with [ and end with ].

Example of the expected JSON output:
[
  {{
    "question": "Text of the question 1 ?",
    "options": {{
      "A": "Option 1",
      "B": "Option 2",
      "C": "Option 3",
      "D": "Option 4"
    }},
    "correct_answer": "B"
  }}
]
"""

# Practice Question prompt
SYSTEM_PROMPT_PRACTICE_QUESTION = """You are a helpful tutor evaluating the user's knowledge.
Based on the provided context, generate ONE specific, open-ended question that tests understanding of key concepts.
CRITICAL RULES:
1. ONLY output the question itself.
2. DO NOT provide the answer.
3. The question must be answerable using only the provided context.
4. Keep the question relatively short and direct.
"""

# Practice Evaluation prompt
SYSTEM_PROMPT_PRACTICE_EVALUATION = """You are a strict but helpful tutor. The user has answered a question based on a specific context.
Evaluate their answer based strictly on the provided context.

CRITICAL JSON RULE : 
You MUST output ONLY valid JSON format. 
Do NOT include any introductory text, greetings, or explanations outside the JSON.
Do NOT wrap the output in markdown code blocks like ```json ... ```. 
Start your response immediately with { and end with }.

Example of the expected JSON output:
{
  "status": "Correct", // Must be exactly "Correct", "Partial", or "Incorrect"
  "feedback": "Your detailed feedback explaining why, what is missing, or correcting mistakes.",
  "expected_answer": "A short version of the ideal answer according to the context."
}
"""

import json
import re

def extract_json_from_llama_response(text):
    
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def build_context(items, tokenizer, question, type , budget_input=DEFAULT_BUDGET_INPUT, **kwargs):

    if type == "qa":
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA
    elif type == "qcm":
        num_questions = kwargs.get("num_questions", 5)
        difficulty = kwargs.get("difficulty", "medium")
        SYSTEM_PROMPT = get_system_prompt_qcm(num_questions, difficulty)
    elif type == "practice_question":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_QUESTION
    elif type == "practice_evaluation":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_EVALUATION
    else:
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA
    

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

    for i, item in enumerate(items, start=1):
        if hasattr(item, "content"):
            page = getattr(item, "source_page", "pas un chunk de document")
            chunk_block = f"Chunk content:\n{item.content} (Page: {page})"
        elif hasattr(item, "definition"):
            chunk_block = f"Concept :\n{item.name}: {item.definition}"
        else:
            continue

        chunk_tokens = count_tokens(chunk_block, tokenizer)

        if total_tokens + chunk_tokens <= budget_input:
            context_parts.append(chunk_block)
            total_tokens += chunk_tokens
        else:
            break

    return "\n\n".join(context_parts)


def generate_answer(context, question, tokenizer, generation_model, type="qa", max_new_tokens=MAX_OUTPUT, **kwargs):
    
    if type == "qa":
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA
    elif type == "qcm":
        num_questions = kwargs.get("num_questions", 5)
        difficulty = kwargs.get("difficulty", "medium")
        SYSTEM_PROMPT = get_system_prompt_qcm(num_questions, difficulty)
    elif type == "practice_question":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_QUESTION
    elif type == "practice_evaluation":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_EVALUATION
    else:
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA

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
    generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=max_new_tokens, do_sample=True)
    thread = Thread(target=generation_model.generate, kwargs=generation_kwargs)
    thread.start()
    # 3. Yield chunks as they arrive
    for new_text in streamer:
        yield new_text
