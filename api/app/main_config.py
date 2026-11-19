from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://unx2:unx2_dev_only@postgres:5432/unx2"
    redis_url: str = "redis://redis:6379/0"
    environment: str = "development"
    jwt_secret: str = "INSECURE_DEVELOPMENT_SECRET_CHANGE_THIS"
    jwt_expire_minutes: int = 60


settings = Settings()
