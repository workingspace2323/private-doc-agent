import os
import pickle
import numpy as np


class VectorStore:
    def __init__(self, path):
        self.path = path
        self.embeddings = None
        self.chunks = None

    def build(self, embeddings, chunks):
        # Ensure numpy array
        self.embeddings = np.array(embeddings, dtype=np.float32)
        self.chunks = chunks

    def save(self):
        os.makedirs(self.path, exist_ok=True)

        with open(os.path.join(self.path, "embeddings.pkl"), "wb") as f:
            pickle.dump(self.embeddings, f)

        with open(os.path.join(self.path, "chunks.pkl"), "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self):
        with open(os.path.join(self.path, "embeddings.pkl"), "rb") as f:
            self.embeddings = pickle.load(f)

        with open(os.path.join(self.path, "chunks.pkl"), "rb") as f:
            self.chunks = pickle.load(f)

    def exists(self):
        return os.path.exists(os.path.join(self.path, "embeddings.pkl"))

    def search(self, query_embedding, k=3):
        if self.embeddings is None or self.chunks is None:
            return []

        # 🔥 FIX: force correct shape
        query_embedding = np.array(query_embedding, dtype=np.float32)

        if query_embedding.ndim == 0:
            return []  # invalid

        if query_embedding.ndim > 1:
            query_embedding = query_embedding.flatten()

        # Normalize embeddings
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []

        query_embedding = query_embedding / query_norm

        embeddings_norm = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        embeddings_norm[embeddings_norm == 0] = 1

        normalized_embeddings = self.embeddings / embeddings_norm

        # Cosine similarity
        scores = np.dot(normalized_embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(scores)[-k:][::-1]

        results = []
        for idx in top_indices:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])

        return results