"""Abstract base class for all Vector DB clients."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: dict


@dataclass
class BenchmarkRecord:
    id: str
    vector: list[float]
    metadata: dict  # access_level, category, source


class VectorDBClient(ABC):
    """
    Uniform interface for every Vector DB we benchmark.
    All implementations must support:
      - insert (batch)
      - search (ANN, with optional metadata filter)
      - count
      - cleanup
    """

    DIM = 1536  # Match OpenAI text-embedding-3-small

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def create_collection(self, name: str) -> None: ...

    @abstractmethod
    def insert(self, records: list[BenchmarkRecord]) -> None: ...

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def drop_collection(self) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...
