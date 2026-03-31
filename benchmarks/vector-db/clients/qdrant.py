from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from .base import VectorDBClient, BenchmarkRecord, SearchResult


COLLECTION = "spike_benchmark"


class QdrantAdapter(VectorDBClient):
    name = "Qdrant"

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self._client: QdrantClient | None = None

    def connect(self) -> None:
        self._client = QdrantClient(host=self.host, port=self.port, timeout=30)

    def create_collection(self, name: str = COLLECTION) -> None:
        self._collection = name
        existing = [c.name for c in self._client.get_collections().collections]
        if name in existing:
            self._client.delete_collection(name)
        self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=self.DIM, distance=Distance.COSINE),
        )

    def insert(self, records: list[BenchmarkRecord]) -> None:
        points = [
            PointStruct(id=i, vector=r.vector, payload=r.metadata)
            for i, r in enumerate(records)
        ]
        # Batch in chunks of 1000
        batch_size = 1000
        for i in range(0, len(points), batch_size):
            self._client.upsert(
                collection_name=self._collection,
                points=points[i : i + batch_size],
            )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        qdrant_filter = None
        if filter:
            must = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter.items()
            ]
            qdrant_filter = Filter(must=must)

        hits = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
        ).points
        return [SearchResult(id=str(h.id), score=h.score, metadata=h.payload) for h in hits]

    def count(self) -> int:
        return self._client.count(collection_name=self._collection).count

    def drop_collection(self) -> None:
        self._client.delete_collection(self._collection)
