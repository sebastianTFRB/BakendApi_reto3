from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Lead Agent API"
    debug: bool = False

    # 🔥 Solo estas dos variables son necesarias para Supabase API
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")  # usa SERVICE_ROLE

    # Opcionales
    supabase_bucket: str = Field("posts", env="SUPABASE_BUCKET")

    # JWT
    secret_key: str = Field("super-secret-key", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # LLM
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
    llm_temperature: float = Field(0.2, env="LLM_TEMPERATURE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
