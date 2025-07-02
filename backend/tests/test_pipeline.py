import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app')))
from app.embeddings import IEmbedder
from app.naming import IFolderNamer
from app.clustering import cluster_embeddings, pick_representative

import pytest
from unittest.mock import MagicMock
import numpy as np

class DummyEmbedder(IEmbedder):
    def embed(self, texts):
        # Return deterministic fake embeddings
        return np.arange(len(texts)*3).reshape(len(texts), 3)

class DummyNamer(IFolderNamer):
    def name_folder(self, samples):
        return "TestFolder"

def test_cluster_and_naming():
    texts = [f"Email {i}" for i in range(10)]
    embedder = DummyEmbedder()
    namer = DummyNamer()
    embeddings = embedder.embed(texts)
    labels = cluster_embeddings(embeddings, n_clusters=2)
    reps = pick_representative(texts, labels, samples_per_cluster=2)
    folder_names = {k: namer.name_folder(samples) for k, samples in reps.items()}
    assert set(folder_names.values()) == {"TestFolder"}
    for k, samples in reps.items():
        assert len(samples) <= 2

def test_embedder_interface():
    embedder = DummyEmbedder()
    arr = embedder.embed(["a", "b"])
    assert arr.shape == (2, 3)

def test_namer_interface():
    namer = DummyNamer()
    name = namer.name_folder(["sample1", "sample2"])
    assert name == "TestFolder"
