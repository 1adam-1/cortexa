def generate_qcm(context, tokenizer, generation_model, max_new_tokens=500):
    messages = [
        {"role": "user", "content": f"Genere 5 questions a choix multiples a partir du contexte suivant.\n\nContexte:\n{context}\n\nChaque question doit contenir :\n- 4 options\n- 1 bonne reponse\n\nRetourne le resultat au format JSON :\n\n{{\n \"question\": \"\",\n \"options\": [\"\",\"\",\"\",\"\"],\n \"answer\": \"\"\n}}"}
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
