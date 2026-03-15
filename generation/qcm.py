def generate_qcm(context, tokenizer, generation_model, max_new_tokens=500):
    prompt = f"""
[INST]
Generate 5 multiple choice questions based on the following context.

Context:
{context}

Each question must contain:
- 4 options
- 1 correct answer
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
