def generate_summary( tokenizer, generation_model, context):

    

    prompt = f"""
    [INST]
    Résume le contenu suivant pour un étudiant.

    Concentre-toi sur :
    - concepts clés
    - définitions importantes
    - idées principales

    Contexte :
    {context}
    [/INST]
    """

    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)
    outputs= generation_model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False,
    )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)