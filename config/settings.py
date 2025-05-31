from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_FILE: str = "database.db"
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    RELOAD: bool = True

    # Toggle settings for various parts of the server
    ENABLE_MIDDLEWARE: bool = True
    ENABLE_API: bool = True
    ENABLE_FRONTEND: bool = True
    ENABLE_DB_QUERIES: bool = True
    ENABLE_WEBSOCKETS: bool = True

    class Config:
        env_file = ".env"

settings = Settings()