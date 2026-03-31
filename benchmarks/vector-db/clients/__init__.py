from .qdrant import QdrantAdapter
from .pgvector import PgvectorAdapter
from .milvus import MilvusAdapter
from .opensearch import OpenSearchAdapter

ALL_CLIENTS = [QdrantAdapter, PgvectorAdapter, MilvusAdapter, OpenSearchAdapter]
