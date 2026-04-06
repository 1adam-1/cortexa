def ask_question(context, tokenizer, generation_model, max_new_tokens=200):
    messages = [
        {"role": "user", "content": f"Genere 3 questions ouvertes qui evaluent la comprehension.\nContexte :\n{context}"}
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
