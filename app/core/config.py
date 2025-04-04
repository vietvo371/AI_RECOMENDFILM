from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_ENV: str = "development"
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    MODEL_PATH: str = "./models"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
