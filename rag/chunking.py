def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def chunk_text_by_tokens(sections, tokenizer, max_tokens=900, min_tokens=100, overlap=1):

    chunks=[]
    for section in sections:
        title = section["title"] or "Untitled"
        type = section.get("type",[])
        items = section["text"]
        pages = section.get("pages", [])

        current_chunk = []
        current_token = 0

        for item in items:
            token_length = count_tokens(item, tokenizer)

            if item.startswith("[TABLE]"):
                if current_chunk:
                    chunks.append({
                        "title": title,
                        "type": type,
                        "text": "\n".join(current_chunk),
                        "pages": pages,
                    })
                    current_chunk = []
                    current_token = 0

                chunks.append({
                    "title": title,
                    "type": type,
                    "text": item,
                    "pages": pages,
                })
                continue

            if current_token + token_length <= max_tokens:
                current_chunk.append(item)
                current_token += token_length

            else:
                if current_token >= min_tokens:
                    chunks.append({
                        "title": title,
                        "type": type,
                        "text": "\n".join(current_chunk),
                        "pages": pages,
                    })
                
                if current_chunk:
                    overlap_tokens = current_chunk[-overlap:]

                    current_chunk = overlap_tokens + [item]
                    current_token = sum( count_tokens(x, tokenizer) for x in current_chunk)

    
        if current_chunk and current_token >= min_tokens:
            chunks.append({
                "title": title,
                "type": type,
                "text": "\n".join(current_chunk),
                "pages": pages,
            })

    return chunks
                

        

                    



    
