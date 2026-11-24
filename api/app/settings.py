from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    database_url: str
    redis_url: str
    environment: str = "development"
    unx2_api_key: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-6.1-terra"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    arbiter_provider: str = "openai"
    provider_timeout_seconds: float = 45.0
    max_prompt_characters: int = 12000


settings = Settings()
