from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_FILE: str = "database.db"
    FASTAPI_HOST: str = "localhost"
    FASTAPI_PORT: int = 8080
    RELOAD: bool = False

    # Toggle settings for various parts of the server
    ENABLE_MIDDLEWARE: bool = True
    ENABLE_API: bool = True
    ENABLE_FRONTEND: bool = True
    ENABLE_DB_QUERIES: bool = True
    ENABLE_WEBSOCKETS: bool = True
    LOG_EXTRA_INFO: bool = True
    LOG_TO_FILE: bool = False

    # CMS schema validation
    # Valid values are "off", "warn", and "enforce"
    CMS_SCHEMA_VALIDATION: str = "warn"

    class Config:
        env_file = ".env"

settings = Settings()