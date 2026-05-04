"""
Configuration module for the Document Intelligence Pipeline.
Loads environment variables and provides centralized settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # LLM Provider
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

    # OCR
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")

    # Pipeline
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_EXTENSIONS: list[str] = [
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
        ".docx", ".xlsx", ".csv", ".html", ".txt", ".md"
    ]

    # Output
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings. Returns list of errors."""
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set. Add it to your .env file.")
        return errors


settings = Settings()
