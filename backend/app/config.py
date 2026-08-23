from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Career Intelligence"
    debug: bool = True

    # Paths
    project_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = project_root / "data"
    uploads_dir: Path = data_dir / "uploads"
    models_dir: Path = project_root / "models"

    # Ollama (free local LLM — optional, Phase 2+)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


settings = Settings()

# Ensure directories exist at import
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)
