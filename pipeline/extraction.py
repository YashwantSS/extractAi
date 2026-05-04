"""
Extraction Module
------------------
Uses an LLM with structured output (Pydantic) to extract typed data
from the document text based on its classified type.
"""
from __future__ import annotations

import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from pipeline.ingestion import DocumentPayload
from schemas.models import get_schema_for_doc_type


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a structured data extraction assistant.\n"
            "The document has been classified as: **{doc_type}**\n\n"
            "Extract all relevant fields from the document text and return "
            "the data as a JSON object matching this schema:\n\n"
            "{schema_description}\n\n"
            "Rules:\n"
            "- Return ONLY valid JSON (no markdown fences).\n"
            "- Use null for fields you cannot determine.\n"
            "- Dates should be in YYYY-MM-DD format when possible.\n"
            "- Monetary amounts should be numbers (no currency symbols).\n"
            "- Be thorough: extract every matching field you can find.",
        ),
        (
            "human",
            "--- DOCUMENT TEXT ---\n{text}\n--- END ---\n\n"
            "--- TABLES (if any) ---\n{tables}\n--- END ---",
        ),
    ]
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(payload: DocumentPayload) -> DocumentPayload:
    """
    Extract structured data from the document using an LLM.
    Populates ``payload.extracted_data`` with the result.
    """
    schema_cls = get_schema_for_doc_type(payload.doc_type)

    # Build a human-readable schema description from the Pydantic model
    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

    # Prepare table text
    tables_text = ""
    for i, table in enumerate(payload.tables):
        tables_text += f"\n[Table {i + 1}]\n"
        for row in table[:50]:  # limit rows to avoid token overflow
            tables_text += " | ".join(str(c) for c in row) + "\n"

    # Truncate text to ~8000 chars
    text = payload.raw_text[:8000]

    chain = EXTRACT_PROMPT | llm
    response = chain.invoke(
        {
            "doc_type": payload.doc_type,
            "schema_description": schema_json,
            "text": text,
            "tables": tables_text or "No tables found.",
        }
    )

    # Parse response into the Pydantic model
    raw_json = _extract_json(response.content)

    try:
        model_instance = schema_cls.model_validate_json(json.dumps(raw_json))
        payload.extracted_data = model_instance.model_dump()
    except Exception as e:
        # Fallback: store raw JSON even if validation fails
        payload.extracted_data = raw_json
        payload.validation_warnings.append(
            f"Extraction produced data that doesn't fully match schema: {e}"
        )

    field_count = len([v for v in payload.extracted_data.values() if v])
    print(f"[Extraction] ✔ Extracted {field_count} populated fields for '{payload.doc_type}'")
    return payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Parse JSON from LLM output, handling markdown fences."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown fence
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding a JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"raw_response": text}
