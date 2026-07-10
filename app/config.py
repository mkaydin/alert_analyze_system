from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_host: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text:latest"
    llm_model: str = "ornith:latest"
    ollama_concurrency: int = 4
    ollama_timeout: int = 60
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    chromadb_path: str = "data/chromadb"
    chromadb_collections: list[str] = [
        "alerts",
        "evidence",
        "rules",
        "flags",
        "documents",
        "feedback",
    ]

    model_config = {"env_prefix": "ALERT_", "env_file": ".env"}


settings = Settings()
