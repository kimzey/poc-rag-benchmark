"""Single source of truth for LLM provider keys — imported by TUI and evaluate.py."""
ALL_PROVIDERS = [
    "openrouter_gpt4o_mini",
    "openrouter_gpt4o",
    "openrouter_claude_sonnet",
    "openrouter_llama3",
    "openrouter_gemini_flash",
    "openrouter_deepseek",
    "openai_gpt4o_mini",
    "openai_gpt4o",
    "anthropic_sonnet",
    "anthropic_haiku",
    "ollama",
]
DEFAULT_PROVIDERS = {"openrouter_gpt4o_mini"}
