import json
import re
import os
import io
import base64
from sqlalchemy import cast, Float

from entities.models import Chunk, Cluster, Cluster_chunk, Concept, db


SYSTEM_PROMPT_SLIDES = """You are an elite presentation designer and cinematic visual director.
Given a list of key concepts from a document, structure them into visually compelling presentation slides.

Your goal is to create slides that feel premium, modern, and visually coherent — like a keynote presentation from a top-tier design agency.

Output ONLY valid JSON. No markdown. No explanations. Start with [ and end with ].

Rules:
- Keep titles concise and impactful (max 6 words).
- Summaries must be clear, informative, and easy to understand in 2–3 sentences.
- image_prompt must be highly detailed, cinematic, and optimized for AI image generation.
- Every image_prompt must:
    - describe the scene composition clearly
    - include subject, environment, lighting, camera angle, depth, textures, mood, and color palette
    - specify a professional visual style
    - avoid generic wording
    - avoid text, captions, labels, watermarks, UI elements, or infographics inside the image
    - match the concept emotionally and visually
    - feel suitable for a high-end business or educational presentation
- Prefer photorealistic or cinematic styles unless the topic strongly benefits from illustration or 3D visualization.
- Images should look polished, modern, and presentation-ready.

Use this exact JSON structure:

[
    {
        "slide_number": 1,
        "title": "Short title",
        "summary": "2-3 sentence explanation of the concept.",
        "image_prompt": "Ultra-detailed cinematic visual description with subject, environment, composition, lighting, mood, materials, camera perspective, depth of field, professional style, realistic textures, and presentation-quality aesthetics. No text in image."
    }
]
"""

def get_concepts_from_document(doc_id):
    concepts = (
    db.session.query(Concept)
    .filter(
        db.session.query(Chunk.id)
        .join(Cluster_chunk, Cluster_chunk.id_chunk == Chunk.id)
        .join(Cluster, Cluster.id == Cluster_chunk.id_cluster)
        .filter(
            Cluster.id == Concept.id_cluster,
            Chunk.id_document == doc_id
        )
        .exists()
    )
    .order_by(cast(Concept.importance, Float).desc())
    .limit(4)
    .all()
)
    return concepts

def build_conceprs(concepts):
    concepts_list = []
    for i,c in enumerate(concepts, start=1):
        importance_val = float(c.importance) if c.importance else 0.0
        concepts_list.append(
            f"Concept {i} (importance: {importance_val:.2f})\n"
            f"Name: {c.name}\n"
            f"Definition: {c.definition}\n"
            f"Keywords: {c.keywords}"
        )
    
    return '\n\n'.join(concepts_list)

def structure_slides(concepts, generation_model, tokenizer, num_slides=4):
    context = build_conceprs(concepts)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SLIDES},
        {
            "role": "user",
            "content": (
                f"NUM_SLIDES: {num_slides}\n\n"
                f"CONCEPTS:\n{context}\n\n"
                "Respond ONLY with valid JSON. Start with [ and end with ]."
            )
        }
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(generation_model.device)
    
    outputs = generation_model.generate(
    **inputs,
    do_sample=False,
    max_new_tokens=1024,
)

    generated_text = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[-1]:],
    skip_special_tokens=True
)

    return generated_text

def parse_slides(raw):
    raw = re.sub(r"```json|```", "", raw).strip()

    # Find the JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in model output:\n{raw}")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse failed: {e}\nRaw output:\n{raw}")
    

from huggingface_hub import InferenceClient


def _get_hf_client():
    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise RuntimeError("HF_API_TOKEN environment variable not set")
    return InferenceClient(token=token)


def generate_slide_image(image_prompt: str) -> bytes:
    client = _get_hf_client()
    image_resp = client.text_to_image(
        prompt=(
            "Professional presentation slide illustration, no text, no labels: "
            f"{image_prompt}. Clean, minimalist, high quality."
        ),
        model="black-forest-labs/FLUX.1-schnell"
    )

   
    buf = io.BytesIO()
    image_resp.save(buf, format="PNG")
    return buf.getvalue()



       
def generate_presentation(doc_id, generation_model, tokenizer):
    concepts = get_concepts_from_document(doc_id)
    if not concepts:
        raise ValueError("No concepts found. Run concept extraction first.")

    raw = structure_slides(concepts, generation_model, tokenizer)
    slides_data = parse_slides(raw)

    # Generate image for each slide
    for slide in slides_data:
        try:
            image_bytes = generate_slide_image(slide.get("image_prompt", ""))
            slide["image_bytes"] = image_bytes  # raw bytes
        except Exception as e:
            # attach a null image and continue; consumer can decide how to handle
            slide["image_bytes"] = None

    return slides_data