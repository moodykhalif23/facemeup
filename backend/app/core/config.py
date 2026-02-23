from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SkinCare AI API"
    env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/skincare"
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl_seconds: int = 300

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    model_saved_path: str = "app/models_artifacts/saved_model"
    model_input_size: int = 224
    model_skin_types: str = "Oily,Dry,Combination,Normal,Sensitive"
    model_conditions: str = "Acne,Hyperpigmentation,Uneven tone,Dehydration,None detected"


settings = Settings()
