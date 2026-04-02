"""Single source of truth for embedding model keys — imported by TUI and evaluate.py."""
ALL_MODELS = [
    "bge_m3",
    "multilingual_e5",
    "mxbai",
    "wangchanberta",
    "openai_large",
    "openai_small",
    "cohere_v3",
]
OPEN_SOURCE_MODELS = {"bge_m3", "multilingual_e5", "mxbai", "wangchanberta"}
