from typing import Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from .base import VectorDBClient, BenchmarkRecord, SearchResult

COLLECTION = "spike_benchmark"


class MilvusAdapter(VectorDBClient):
    name = "Milvus"

    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self._collection: Collection | None = None
        self._collection_name = COLLECTION

    def connect(self) -> None:
        connections.connect(alias="default", host=self.host, port=self.port)

    def create_collection(self, name: str = COLLECTION) -> None:
        self._collection_name = name
        if utility.has_collection(name):
            utility.drop_collection(name)

        schema = CollectionSchema(
            fields=[
                FieldSchema("id", DataType.INT64, is_primary=True),
                FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=self.DIM),
                FieldSchema("access_level", DataType.VARCHAR, max_length=32),
                FieldSchema("category", DataType.VARCHAR, max_length=64),
                FieldSchema("source", DataType.VARCHAR, max_length=256),
            ],
            description="Spike benchmark collection",
        )
        self._collection = Collection(name=name, schema=schema)
        self._collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 64},
            },
        )

    def insert(self, records: list[BenchmarkRecord]) -> None:
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            self._collection.insert([
                [j + i for j in range(len(batch))],         # id
                [r.vector for r in batch],                   # embedding
                [r.metadata.get("access_level", "") for r in batch],
                [r.metadata.get("category", "") for r in batch],
                [r.metadata.get("source", "") for r in batch],
            ])
        self._collection.flush()

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        self._collection.load()
        expr = None
        if filter:
            parts = [f'{k} == "{v}"' for k, v in filter.items()]
            expr = " && ".join(parts)

        results = self._collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=top_k,
            expr=expr,
            output_fields=["access_level", "category", "source"],
        )
        hits = results[0]
        return [
            SearchResult(
                id=str(h.id),
                score=h.score,
                metadata={f: h.entity.get(f) for f in ["access_level", "category", "source"]},
            )
            for h in hits
        ]

    def count(self) -> int:
        self._collection.flush()
        return self._collection.num_entities

    def drop_collection(self) -> None:
        if self._collection:
            self._collection.drop()
