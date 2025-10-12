from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Loads environment variables from the .env file for configuration.
    """
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@host:port/dbname" # Default placeholder

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
