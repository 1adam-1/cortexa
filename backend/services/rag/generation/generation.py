from entities.models import Chunk
from threading import Thread 
from transformers import TextIteratorStreamer

MODEL_LIMIT = 8192
MAX_OUTPUT = 1024
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN

#Q/A prompt
SYSTEM_PROMPT_QA = """
You are a direct, concise, and professional multilingual RAG assistant.

Rules:
- Answer ONLY using the provided context. Do not use outside knowledge.
- The context must DIRECTLY and SPECIFICALLY address the question.
- If the context only mentions the topic incidentally or as a side reference, 
  treat it as missing and refuse.
- If the context does not contain a direct answer, reply ONLY with a polite 
  statement saying the information is missing. Nothing else.
- If TARGET_LANGUAGE is provided, answer STRICTLY in that language.
- Otherwise, detect the language of the QUESTION and answer STRICTLY in that same language.
- Be concise and objective.
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

#Summary prompt
SYSTEM_PROMPT_SUMMARY = """You are a highly skilled document summarization assistant.
CRITICAL RULES:
- Provide a concise, clear, and comprehensive summary of the provided context.
- Highlight the main concepts, findings, and arguments.
- Do not invent or hallucinate information. You must rely strictly on the provided context.
- Maintain a professional and objective tone.
- Keep the summary well-structured, using bullet points for key takeaways if appropriate.
- If TARGET_LANGUAGE is provided, answer STRICTLY in that language.
- Otherwise, detect the language of the QUESTION and answer STRICTLY in that same language.
"""

#no context for answer prompt
SYSTEM_PROMPT_NO_CONTEXT = """You are a multilingual assistant.
Your only task is to politely inform the user that the document does not contain 
information to answer their question.
Output ONLY that single sentence. Nothing else. No explanation. No apology.
If TARGET_LANGUAGE is provided, answer STRICTLY in that language.
"""

import json
import re

LANGUAGE_CODE_TO_NAME = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "tr": "Turkish",
    "nl": "Dutch",
    "pl": "Polish",
}

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


def _build_language_directive(target_language_code):
    if not target_language_code:
        return ""

    code = str(target_language_code).strip().lower()
    if not code or code == "auto":
        return ""

    language_name = LANGUAGE_CODE_TO_NAME.get(code, "Unknown")
    return f"TARGET_LANGUAGE: {language_name} ({code})"


def build_context(items, tokenizer, question, type ,is_refused=False, budget_input=DEFAULT_BUDGET_INPUT, **kwargs):

    if is_refused:
        return ""

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
    elif type == "summary":
        SYSTEM_PROMPT = SYSTEM_PROMPT_SUMMARY
    else:
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA

    chunks =[item for item in items if hasattr(item, "content")]
    concepts = [item for item in items if hasattr(item, "definition")]

    chunks = sorted(chunks, key=lambda x: getattr(x, 'rerank_score', 0), reverse=True)
    concepts = sorted(concepts, key=lambda x: getattr(x, 'rerank_score', 0), reverse=True)

    language_directive = ""
    
    language_directive = _build_language_directive(kwargs.get("target_language_code"))
    print(f"Language directive: {language_directive}")

    language_block = f"{language_directive}\n\n" if language_directive else ""
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"""
            QUESTION:
            {question}
            
            {language_block}CONTEXT:
            
            CRITICAL: Output the answer directly in TARGET_LANGUAGE if provided, otherwise use the QUESTION language. Translate as needed. Do NOT introduce your answer (e.g., no "The answer is...").
        """
        }
    ]
    
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    context_part = []
    remaining_budget = budget_input - count_tokens(prompt, tokenizer)
    for i,chunk in enumerate(chunks, start =1):
        page_number = getattr(chunk, "source_page", "N/A")
        chunk_text = f"Chunk {i} (Page {page_number}): {chunk.content}\n"
        chunk_tokens = count_tokens(chunk_text, tokenizer)

        if chunk_tokens <= remaining_budget:
            context_part.append(chunk_text)
            remaining_budget -= chunk_tokens
        else:
            break
    
    concept_parts = []
    for i,concept in enumerate(concepts, start=1):
        concept_text = f"Concept {i} - {concept.name}: {concept.definition}\n"
        concept_tokens = count_tokens(concept_text, tokenizer)

        if concept_tokens <= remaining_budget:
            concept_parts.append(concept_text)
            remaining_budget -= concept_tokens
        else:
            break
    
    if concept_parts:
        context_part.append('\nRelevant Concepts:\n')
        context_part.extend(concept_parts)

    return '\n\n'.join(context_part)


def generate_answer(context, question, tokenizer, generation_model, type="qa", is_refused=False, max_new_tokens=MAX_OUTPUT, **kwargs):
    
    if is_refused:
        SYSTEM_PROMPT = SYSTEM_PROMPT_NO_CONTEXT
        context = ""
        question='The document does not contain information to answer the question. Please politely inform the user of this fact in a single sentence.'
    elif type == "qa":
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA
    elif type == "qcm":
        num_questions = kwargs.get("num_questions", 5)
        difficulty = kwargs.get("difficulty", "medium")
        SYSTEM_PROMPT = get_system_prompt_qcm(num_questions, difficulty)
    elif type == "practice_question":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_QUESTION
    elif type == "practice_evaluation":
        SYSTEM_PROMPT = SYSTEM_PROMPT_PRACTICE_EVALUATION
    elif type == "summary":
        SYSTEM_PROMPT = SYSTEM_PROMPT_SUMMARY
    else:
        SYSTEM_PROMPT = SYSTEM_PROMPT_QA



    language_directive = ""
    
    language_directive = _build_language_directive(kwargs.get("target_language_code"))

    system_content = SYSTEM_PROMPT
    if language_directive:
        system_content = f"{SYSTEM_PROMPT}\n{language_directive}\nYou MUST answer only in TARGET_LANGUAGE."

    language_block = f"{language_directive}\n\n" if language_directive else ""
    messages = [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": f"""QUESTION:
    {question}

    {language_block}CONTEXT:
    {context}

    CRITICAL: Output the answer directly in TARGET_LANGUAGE if provided, otherwise use the QUESTION language. Translate as needed. Do NOT introduce your answer (e.g., no "The answer is...").
        """
        }]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)

    # 1. Initialize the streamer
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    # 2. Run generation in a separate thread because .generate() is blocking
    generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=max_new_tokens, do_sample=False,temperature=0.0,repetition_penalty=1.1)
    thread = Thread(target=generation_model.generate, kwargs=generation_kwargs)
    thread.start()
    # 3. Yield chunks as they arrive
    for new_text in streamer:
        yield new_text
