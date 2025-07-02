from typing import List, Protocol
import numpy as np
from sentence_transformers import SentenceTransformer

class IEmbedder(Protocol):
    def embed(self, texts: List[str]) -> np.ndarray:
        ...

class LocalEmbedder(IEmbedder):
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    def embed(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)
