from sentence_transformers import SentenceTransformer

# SMALL + FAST MODEL (VERY IMPORTANT)
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts):
    return model.encode(texts).tolist()