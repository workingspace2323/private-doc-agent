import os
import json
import numpy as np


class VectorStore:
    def __init__(self, path):
        self.path = path
        self.vectors = []
        self.metadata = []

    def build(self, embeddings, chunks):
        self.vectors = embeddings
        self.metadata = chunks

    def save(self):
        os.makedirs(self.path, exist_ok=True)

        with open(os.path.join(self.path, "vectors.json"), "w") as f:
            json.dump(self.vectors, f)

        with open(os.path.join(self.path, "meta.json"), "w") as f:
            json.dump(self.metadata, f)

    def load(self):
        with open(os.path.join(self.path, "vectors.json"), "r") as f:
            self.vectors = json.load(f)

        with open(os.path.join(self.path, "meta.json"), "r") as f:
            self.metadata = json.load(f)

    def exists(self):
        return os.path.exists(os.path.join(self.path, "vectors.json"))

    def search(self, query_vector, k=3):
        vectors = np.array(self.vectors)
        query = np.array(query_vector)

        scores = np.dot(vectors, query) / (
            np.linalg.norm(vectors, axis=1) * np.linalg.norm(query) + 1e-10
        )

        top_k = np.argsort(scores)[-k:][::-1]

        return [self.metadata[i] for i in top_k]