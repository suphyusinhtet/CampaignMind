import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

class Settings:
    """
    Single source of truth for all CampaignMind configuration.
    Configured for Gemini as the primary LLM via OpenAI-compatible API.
    """

    # ── Gemini ───────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    # Gemini OpenAI-compatible endpoint
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # ── Supabase ─────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")            # anon key
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")  # service role key

    # ── App ──────────────────────────────────────────────────
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FRONTEND_URLS: str = os.getenv("FRONTEND_URLS", "")
    ENABLE_GUEST_MODE: bool = os.getenv("ENABLE_GUEST_MODE", "true").strip().lower() != "false"

    # ── Paths ────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).parent.parent
    VECTOR_DB_PATH: str = os.getenv(
        "VECTOR_DB_PATH",
        str(Path(__file__).parent.parent / "data" / "vectordb")
    )
    RAW_DOCS_PATH: str = os.getenv(
        "RAW_DOCS_PATH",
        str(Path(__file__).parent.parent / "data" / "raw_docs")
    )

    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000

    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5

    MAX_AGENT_TURNS: int = 10
    AGENT_TIMEOUT: int = 120

    def validate(self) -> bool:
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Get one at https://aistudio.google.com/apikey"
            )
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not set.")
        if not self.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY is not set.")
        return True

    def summary(self) -> str:
        return (
            f"\nCampaignMind Settings\n"
            f"{'='*40}\n"
            f"  ENV:           {self.APP_ENV}\n"
            f"  MODEL:         {self.MODEL_NAME}\n"
            f"  BASE_URL:      {self.GEMINI_BASE_URL}\n"
            f"  VECTOR_DB:     {self.VECTOR_DB_PATH}\n"
            f"  RAW_DOCS:      {self.RAW_DOCS_PATH}\n"
            f"  API_KEY SET:   {'yes ✓' if self.GEMINI_API_KEY else 'NO - MISSING ✗'}\n"
            f"  SUPABASE:      {'set ✓' if self.SUPABASE_URL else 'NO - MISSING ✗'}\n"
            f"{'='*40}\n"
        )

settings = Settings()
