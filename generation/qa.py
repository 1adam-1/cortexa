MODEL_LIMIT = 4096
MAX_OUTPUT = 300
SAFETY_MARGIN = 50
DEFAULT_BUDGET_INPUT = MODEL_LIMIT - MAX_OUTPUT - SAFETY_MARGIN


def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def build_context(chunks, tokenizer, question=None, budget_input=DEFAULT_BUDGET_INPUT, prompt=None):
    if prompt is None:
        prompt = f"""
[INST]
Tu es un assistant RAG.

Reponds uniquement avec les informations du contexte.
Si l'information n'est pas dans le contexte, dis \"Je ne sais pas\".

Reponds en francais.

Question:
{question}

Contexte:

[/INST]
"""

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
    prompt = f"""
[INST]
Tu es un assistant RAG.

Reponds uniquement avec les informations du contexte.
Si l'information n'est pas dans le contexte, dis \"Je ne sais pas\".

Reponds en francais.

Question:
{question}

Contexte:
{context}
[/INST]
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)

    outputs = generation_model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
    )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)
