from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str
    TAVILY_API_KEY: str

    GROQ_MODEL: str = "openai/gpt-oss-120b"

    MAX_RETRIES: int = 2
    MAX_SEARCH_RESULTS: int = 5
    REQUEST_TIMEOUT: int = 15

    # Caps extracted page text so a single fetched article cannot blow
    # past the LLM's token-per-minute rate limit downstream.
    MAX_PAGE_TEXT_CHARS: int = 4000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()