from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:3000"

    # Cookie names — centralised so frontend + backend always agree
    ACCESS_TOKEN_COOKIE: str = "access_token"
    REFRESH_TOKEN_COOKIE: str = "refresh_token"

    # RAG: embeddings (Voyage) + chat (Anthropic)
    VOYAGE_API_KEY: str
    ANTHROPIC_API_KEY: str
    EMBEDDING_MODEL: str = "voyage-3-lite"
    EMBEDDING_DIM: int = 512
    CHAT_MODEL: str = "claude-sonnet-5"
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 50
    TOP_K: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
