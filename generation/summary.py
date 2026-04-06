def generate_summary( tokenizer, generation_model, context):

    

    messages = [
        {"role": "user", "content": f"Résume le contenu suivant pour un étudiant.\n\nConcentre-toi sur :\n- concepts clés\n- définitions importantes\n- idées principales\n\nContexte :\n{context}"}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)
    outputs= generation_model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False,
    )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)