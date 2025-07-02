import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict

def cluster_embeddings(embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
    km = KMeans(n_clusters=n_clusters, random_state=0)
    return km.fit_predict(embeddings)

def pick_representative(texts: List[str], labels: np.ndarray, samples_per_cluster=3) -> Dict[int, List[str]]:
    reps: Dict[int, List[str]] = {}
    for k in set(labels):
        cluster_texts = [t for t, l in zip(texts, labels) if l == k]
        reps[k] = cluster_texts[:samples_per_cluster]
    return reps
