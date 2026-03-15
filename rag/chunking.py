def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def chunk_text_by_tokens(
    text,
    tokenizer,
    target_tokens=900,
    min_tokens=120,
    overlap_ratio=0.15,
):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        tokens = tokenizer.encode(para, add_special_tokens=False)
        token_len = len(tokens)

        if token_len < 5:
            continue

        if current_tokens + token_len <= target_tokens:
            current_chunk.append(para)
            current_tokens += token_len
        else:
            chunk_text = "\n".join(current_chunk)

            if current_tokens >= min_tokens:
                chunks.append(chunk_text)

            overlap_tokens = int(target_tokens * overlap_ratio)
            overlap_text = tokenizer.decode(tokenizer.encode(chunk_text)[-overlap_tokens:])

            current_chunk = [overlap_text, para]
            current_tokens = count_tokens(overlap_text, tokenizer) + token_len

    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        if count_tokens(chunk_text, tokenizer) >= min_tokens:
            chunks.append(chunk_text)

    return chunks
