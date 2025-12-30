import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CCCGJ Web"
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-super-secret-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")
    
    # Altcha
    ALTCHA_SECRET: str = os.environ.get("ALTCHA_SECRET", "cccgj-secret-key-12345")
    ALTCHA_COMPLEXITY: int = int(os.environ.get("ALTCHA_COMPLEXITY", 100000))

    class Config:
        case_sensitive = True

    @property
    def assemble_db_connection(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Local Development Fallback -> SQLite
        import pathlib
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        instance_path = os.path.join(base_dir, 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'app.db')
        
        if os.name == 'nt':
             return 'sqlite:///' + str(db_path).replace('\\', '/')
        else:
             return 'sqlite:///' + str(db_path)

@lru_cache()
def get_settings():
    return Settings()
