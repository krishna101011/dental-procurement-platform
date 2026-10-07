from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dental.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-only-change-me"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
