from typing import Optional
from opensearchpy import OpenSearch, helpers
from .base import VectorDBClient, BenchmarkRecord, SearchResult

INDEX = "spike_benchmark"


class OpenSearchAdapter(VectorDBClient):
    name = "OpenSearch"

    def __init__(self, host: str = "localhost", port: int = 9200):
        self.host = host
        self.port = port
        self._client: OpenSearch | None = None
        self._index = INDEX

    def connect(self) -> None:
        self._client = OpenSearch(
            hosts=[{"host": self.host, "port": self.port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            timeout=60,
        )

    def create_collection(self, name: str = INDEX) -> None:
        self._index = name
        if self._client.indices.exists(index=name):
            self._client.indices.delete(index=name)

        self._client.indices.create(
            index=name,
            body={
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 64,
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                    }
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": self.DIM,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {"ef_construction": 64, "m": 16},
                            },
                        },
                        "access_level": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "source": {"type": "keyword"},
                    }
                },
            },
        )

    def insert(self, records: list[BenchmarkRecord]) -> None:
        actions = [
            {
                "_index": self._index,
                "_id": str(i),
                "_source": {
                    "embedding": r.vector,
                    **r.metadata,
                },
            }
            for i, r in enumerate(records)
        ]
        helpers.bulk(self._client, actions, chunk_size=500, request_timeout=120)
        self._client.indices.refresh(index=self._index)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        knn_query: dict = {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": top_k,
                }
            }
        }

        if filter:
            must_terms = [{"term": {k: v}} for k, v in filter.items()]
            query_body = {
                "query": {
                    "bool": {
                        "must": [knn_query],
                        "filter": must_terms,
                    }
                }
            }
        else:
            query_body = {"query": knn_query}

        resp = self._client.search(
            index=self._index,
            body={**query_body, "size": top_k},
        )
        hits = resp["hits"]["hits"]
        return [
            SearchResult(
                id=h["_id"],
                score=h["_score"],
                metadata=h["_source"],
            )
            for h in hits
        ]

    def count(self) -> int:
        resp = self._client.count(index=self._index)
        return resp["count"]

    def drop_collection(self) -> None:
        if self._client.indices.exists(index=self._index):
            self._client.indices.delete(index=self._index)
