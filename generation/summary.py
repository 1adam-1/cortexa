def summarize_chunk(chunk, tokenizer, generation_model, max_new_tokens=150):
    prompt = f"""
[INST]
Vous etes assistant(e) pedagogique.

Resumez le contenu pedagogique suivant.

Concentrez-vous sur:
- les concepts cles
- les definitions importantes
- les idees que les eleves doivent retenir

Content:
{chunk}
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


def generate_summary(chunks, tokenizer, generation_model, top_n=8):
    summaries = []

    for chunk in chunks[:top_n]:
        s = summarize_chunk(chunk["text"], tokenizer, generation_model)
        summaries.append(s)

    combined = "\n".join(summaries)

    prompt = f"""
[INST]
Vous etes assistant(e) pedagogique.

Resumez le contenu pedagogique suivant.

Concentrez-vous sur:
- les concepts cles
- les definitions importantes
- les idees que les eleves doivent retenir

Notes:
{combined}
[/INST]
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)
    outputs = generation_model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False,
    )
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)
