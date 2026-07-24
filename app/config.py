from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="anthropic", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="claude-sonnet-4-6", alias="LLM_MODEL")

    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        alias="EMBEDDING_MODEL",
    )

    faiss_index_dir: str = Field(
        default=str(BASE_DIR / "faiss_index"),
        alias="FAISS_INDEX_DIR",
    )

    audit_db_path: str = Field(
        default=str(BASE_DIR / "audit_logs.db"),
        alias="AUDIT_DB_PATH",
    )

    raw_docs_dir: str = Field(
        default=str(BASE_DIR / "data" / "raw_guidelines"),
        alias="RAW_DOCS_DIR",
    )

    top_k: int = Field(default=8, alias="TOP_K")
    score_threshold: float = Field(default=0.25, alias="SCORE_THRESHOLD")

    api_keys: str = Field(default="demo-key-123", alias="API_KEYS")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def valid_api_keys(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()