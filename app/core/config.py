from pydantic_settings import BaseSettings
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    
    # Default values
    DATABASE_URL: str = "sqlite:///./data/normalized/stcp.db"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    GTFS_DATA_DIR: Path = _project_root / "data" / "raw" / "stcp"
    
    class Config:
        env_file = str(_project_root / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()