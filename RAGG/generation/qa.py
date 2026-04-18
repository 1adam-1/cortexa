MODEL_LIMIT = 8192
MAX_OUTPUT = 300
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN


def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def build_context(chunks, tokenizer, question=None, budget_input=DEFAULT_BUDGET_INPUT, prompt=None):
    if prompt is None:
        messages = [
            {
        "role": "system",
        "content": """Tu es un assistant RAG strict.

        RÈGLES OBLIGATOIRES :
        1. Réponds UNIQUEMENT avec les informations présentes dans le contexte.
        2. Si la réponse n'est pas explicitement dans le contexte, réponds EXACTEMENT : "Je ne sais pas".
        3. N'invente rien. N'utilise aucune connaissance externe.
        4. Cite les passages du contexte utilisés si possible.
        5. Réponds par la langue de la question."""
    },
       {
        "role": "user",
        "content": f"""QUESTION:
        {question}

        CONTEXTE:

        RÉPONSE:"""
    }
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    total_tokens = count_tokens(prompt, tokenizer)
    context_parts = []

    for i, c in enumerate(chunks, start=1):
        chunk_block = f"Extrait {i}:\n{c['text']}"
        chunk_tokens = count_tokens(chunk_block, tokenizer)

        if total_tokens + chunk_tokens <= budget_input:
            context_parts.append(chunk_block)
            total_tokens += chunk_tokens
        else:
            break

    return "\n\n".join(context_parts)


def generate_answer(context, question, tokenizer, generation_model, max_new_tokens=200):
    messages = [
    {
        "role": "system",
        "content": """Tu es un assistant RAG strict.

        RÈGLES OBLIGATOIRES :
        1. Réponds UNIQUEMENT avec les informations présentes dans le contexte.
        2. Si la réponse n'est pas explicitement dans le contexte, réponds EXACTEMENT : "Je ne sais pas".
        3. N'invente rien. N'utilise aucune connaissance externe.
        4. Cite les passages du contexte utilisés si possible.
        5. Réponds en français."""
    },
    {
        "role": "user",
        "content": f"""QUESTION:
        {question}

        CONTEXTE:
        {context}

        RÉPONSE:"""
    }
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)

    outputs = generation_model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
    )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)
