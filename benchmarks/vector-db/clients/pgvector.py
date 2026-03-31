import json
from typing import Optional
import psycopg2
from pgvector.psycopg2 import register_vector
from .base import VectorDBClient, BenchmarkRecord, SearchResult

TABLE = "spike_benchmark"


class PgvectorAdapter(VectorDBClient):
    name = "pgvector"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5433,
        dbname: str = "vectordb",
        user: str = "spike",
        password: str = "spike",
    ):
        self.dsn = f"host={host} port={port} dbname={dbname} user={user} password={password}"
        self._conn = None
        self._table = TABLE

    def connect(self) -> None:
        self._conn = psycopg2.connect(self.dsn)
        self._conn.autocommit = False
        register_vector(self._conn)

    def create_collection(self, name: str = TABLE) -> None:
        self._table = name
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"DROP TABLE IF EXISTS {self._table}")
            cur.execute(f"""
                CREATE TABLE {self._table} (
                    id          BIGINT PRIMARY KEY,
                    embedding   vector({self.DIM}),
                    access_level TEXT,
                    category    TEXT,
                    source      TEXT
                )
            """)
            cur.execute(f"""
                CREATE INDEX ON {self._table}
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        self._conn.commit()

    def insert(self, records: list[BenchmarkRecord]) -> None:
        batch_size = 500
        with self._conn.cursor() as cur:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                args = [
                    (
                        idx + i,
                        r.vector,
                        r.metadata.get("access_level"),
                        r.metadata.get("category"),
                        r.metadata.get("source"),
                    )
                    for idx, r in enumerate(batch)
                ]
                cur.executemany(
                    f"INSERT INTO {self._table} (id, embedding, access_level, category, source) "
                    f"VALUES (%s, %s, %s, %s, %s)",
                    args,
                )
        self._conn.commit()

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        where = ""
        params: list = [query_vector, top_k]
        if filter:
            clauses = []
            for k, v in filter.items():
                clauses.append(f"{k} = %s")
                params.insert(-1, v)
            where = "WHERE " + " AND ".join(clauses)

        sql = f"""
            SELECT id, access_level, category, source,
                   1 - (embedding <=> %s::vector) AS score
            FROM {self._table}
            {where}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        # Adjust params: query_vector used twice (score + order)
        p = [query_vector] + ([v for v in filter.values()] if filter else []) + [query_vector, top_k]
        with self._conn.cursor() as cur:
            cur.execute(sql, p)
            rows = cur.fetchall()

        return [
            SearchResult(
                id=str(r[0]),
                score=float(r[4]),
                metadata={"access_level": r[1], "category": r[2], "source": r[3]},
            )
            for r in rows
        ]

    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._table}")
            return cur.fetchone()[0]

    def drop_collection(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {self._table}")
        self._conn.commit()
