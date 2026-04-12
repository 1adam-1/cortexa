from backend.entities.models import Chunk, db

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text, truncation=False))


def chunk_text_by_tokens(document_id,sections, tokenizer, max_tokens=900, min_tokens=100, overlap=1):

    chunks=[]
    for section in sections:
        title = section["title"] or "Untitled"
        types = section.get("types",[])
        items = section["text"]
        pages = section.get("pages", [])

        current_chunk = []
        current_token = 0

        for item in items:
            token_length = count_tokens(item, tokenizer)

            if item.startswith("[TABLE]"):
                if current_chunk:
                    #save the chunk in the database
                    new_chunk = Chunk(id_document=document_id,
                                    title=title,
                                    content="\n".join(current_chunk),
                                    type=types,
                                    token_count=current_token,
                                    source_page=pages)

                    db.session.add(new_chunk)
                    db.session.commit()

                    chunks.append({
                        "id": new_chunk.id,
                        "title": title,
                        "types": types,
                        "text": "\n".join(current_chunk),
                        "pages": pages,
                    })
                   

                    current_chunk = []
                    current_token = 0
                #save the chunk in the database
                new_chunk = Chunk(id_document=document_id,
                                title=title,
                                content=item,
                                type=types,
                                token_count=token_length,
                                source_page=pages)

                db.session.add(new_chunk)
                db.session.commit()

                chunks.append({
                    "id": new_chunk.id,
                    "title": title,
                    "type": types,
                    "text": item,
                    "pages": pages,
                })
                
                continue

            if current_token + token_length <= max_tokens:
                current_chunk.append(item)
                current_token += token_length

            else:
                if current_token >= min_tokens:
                    #save the chunk in the database
                    new_chunk = Chunk(id_document=document_id,
                                    title=title,
                                    content="\n".join(current_chunk),
                                    type=types,
                                    token_count=current_token,
                                    source_page=pages)

                    db.session.add(new_chunk)
                    db.session.commit()
                    chunks.append({
                        "id": new_chunk.id,
                        "title": title,
                        "types": types,
                        "text": "\n".join(current_chunk),
                        "pages": pages,
                    })

                
                if current_chunk:
                    overlap_tokens = current_chunk[-overlap:]

                    current_chunk = overlap_tokens + [item]
                    current_token = sum( count_tokens(x, tokenizer) for x in current_chunk)

    
        if current_chunk and current_token >= min_tokens:
            #save the chunk in the database
            new_chunk = Chunk(id_document=document_id,
                            title=title,
                            content="\n".join(current_chunk),
                            type=types,
                            token_count=current_token,
                            source_page=pages)

            db.session.add(new_chunk)
            db.session.commit()
            chunks.append({
                "id": new_chunk.id,
                "title": title,
                "type": types,
                "text": "\n".join(current_chunk),
                "pages": pages,
            })

    return chunks
                
