"""
Generate synthetic benchmark dataset.

Each record has:
  - vector: random unit vector (dim=1536, mimics OpenAI embedding)
  - metadata:
      access_level: public | internal | confidential
      category:     tech | hr | finance | ops
      source:       doc_{id}

Design mirrors our permission control use case — so filtered search
benchmarks directly measure production-relevant overhead.
"""
import numpy as np
from ..clients.base import BenchmarkRecord

ACCESS_LEVELS = ["public", "internal", "confidential"]
CATEGORIES = ["tech", "hr", "finance", "ops"]

# Probability weights (skewed toward public — realistic distribution)
ACCESS_WEIGHTS = [0.5, 0.35, 0.15]
CATEGORY_WEIGHTS = [0.4, 0.2, 0.2, 0.2]


def generate_dataset(n: int, dim: int = 1536, seed: int = 42) -> list[BenchmarkRecord]:
    """Return n BenchmarkRecord objects with unit-normalized random vectors."""
    rng = np.random.default_rng(seed)

    raw = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    vectors = (raw / norms).tolist()

    access_levels = rng.choice(ACCESS_LEVELS, size=n, p=ACCESS_WEIGHTS).tolist()
    categories = rng.choice(CATEGORIES, size=n, p=CATEGORY_WEIGHTS).tolist()

    return [
        BenchmarkRecord(
            id=str(i),
            vector=vectors[i],
            metadata={
                "access_level": access_levels[i],
                "category": categories[i],
                "source": f"doc_{i:06d}",
            },
        )
        for i in range(n)
    ]


def generate_queries(n: int, dim: int = 1536, seed: int = 99) -> list[list[float]]:
    """Return n random unit vectors to use as query vectors."""
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    return (raw / norms).tolist()


def compute_ground_truth(
    dataset: list[BenchmarkRecord],
    queries: list[list[float]],
    top_k: int = 10,
) -> list[set[str]]:
    """
    Brute-force exact nearest neighbours using numpy.
    Used to compute recall@k against ANN results.
    Only practical for small datasets (≤50K).
    """
    corpus = np.array([r.vector for r in dataset], dtype=np.float32)  # (N, D)
    q_mat = np.array(queries, dtype=np.float32)                        # (Q, D)

    # Cosine similarity = dot product (vectors are unit-normalised)
    scores = q_mat @ corpus.T  # (Q, N)

    ground_truth = []
    for row in scores:
        top_ids = np.argpartition(row, -top_k)[-top_k:]
        ground_truth.append({str(i) for i in top_ids})
    return ground_truth
