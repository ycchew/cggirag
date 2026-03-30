import os
from typing import Optional
from pathlib import Path


def _load_env_vars():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv

        config_dir = Path(__file__).parent
        project_root = (
            config_dir.parent
            if config_dir.name == "config"
            else config_dir.parent.parent
        )

        env_paths = [
            project_root / ".env",
            Path.cwd() / ".env",
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                return

        load_dotenv(override=True)
    except ImportError:
        pass


_load_env_vars()


class Settings:
    # Database settings
    POSTGRES_URL: str = os.getenv(
        "POSTGRES_URL", "postgresql://user:password@localhost:5432/cggi_db"
    )
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "http://localhost:8000")

    # API settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/api/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-max")

    # Application settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Vector database settings
    VECTOR_EMBEDDING_DIMENSION: int = 1536  # Dimension of embeddings

    # Document processing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Search settings
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SEARCH_THRESHOLD: float = float(os.getenv("SEARCH_THRESHOLD", "0.7"))


settings = Settings()
