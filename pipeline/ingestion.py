"""
Ingestion Module
-----------------
Accepts documents of any supported type, validates file size and extension,
and returns a standardized DocumentPayload for downstream stages.
"""
from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass, field
from pathlib import Path

from config import settings


@dataclass
class DocumentPayload:
    """Standardized container passed through every pipeline stage."""

    file_path: str
    file_name: str
    file_extension: str
    mime_type: str | None
    file_size_bytes: int

    # Populated by later stages
    raw_text: str = ""
    tables: list[list[list[str]]] = field(default_factory=list)  # list of 2-D tables
    doc_type: str = ""            # e.g. "invoice", "contract", "receipt"
    doc_summary: str = ""
    extracted_data: dict = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class IngestionError(Exception):
    """Raised when a document cannot be ingested."""


def ingest(file_path: str) -> DocumentPayload:
    """
    Validate and wrap a file into a DocumentPayload.

    Parameters
    ----------
    file_path : str
        Path to the document on disk.

    Returns
    -------
    DocumentPayload

    Raises
    ------
    IngestionError
        If the file does not exist, is too large, or has an unsupported extension.
    """
    path = Path(file_path).resolve()

    # --- existence check ---
    if not path.exists():
        raise IngestionError(f"File not found: {path}")

    if not path.is_file():
        raise IngestionError(f"Path is not a file: {path}")

    # --- extension check ---
    ext = path.suffix.lower()
    if ext not in settings.SUPPORTED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(settings.SUPPORTED_EXTENSIONS)}"
        )

    # --- size check ---
    size = path.stat().st_size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise IngestionError(
            f"File size ({size / 1024 / 1024:.1f} MB) exceeds "
            f"maximum ({settings.MAX_FILE_SIZE_MB} MB)."
        )

    # --- MIME type ---
    mime, _ = mimetypes.guess_type(str(path))

    payload = DocumentPayload(
        file_path=str(path),
        file_name=path.name,
        file_extension=ext,
        mime_type=mime,
        file_size_bytes=size,
    )

    print(f"[Ingestion] ✔ Accepted '{path.name}' ({ext}, {size/1024:.1f} KB)")
    return payload
