from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    project_name: str = "Lead Agent API"
    debug: bool = False
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    secret_key: str = Field("super-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    supabase_url: str = Field("", env="SUPABASE_URL")
    supabase_key: str = Field("", env="SUPABASE_KEY")
    supabase_bucket: str = Field("posts", env="SUPABASE_BUCKET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
