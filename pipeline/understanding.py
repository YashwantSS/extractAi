"""
Understanding Module
---------------------
Sends parsed text to an LLM to:
  1. Classify the document type (invoice, receipt, contract, report, etc.)
  2. Produce a short summary
  3. Identify key sections / entities present
"""
from __future__ import annotations

import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from pipeline.ingestion import DocumentPayload

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a document intelligence assistant. "
            "Analyze the following document text and return a JSON object with:\n"
            '  "doc_type": one of ["invoice", "receipt", "contract", "report", '
            '"letter", "resume", "form", "bank_statement", "medical_record", "other"],\n'
            '  "summary": a 2-3 sentence summary of the document,\n'
            '  "sections": a list of key section/entity names found in the document,\n'
            '  "confidence": a float 0-1 indicating your confidence in the classification.\n'
            "Return ONLY valid JSON, no markdown fences.",
        ),
        (
            "human",
            "--- DOCUMENT TEXT (first 6000 chars) ---\n{text}\n--- END ---",
        ),
    ]
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def understand(payload: DocumentPayload) -> DocumentPayload:
    """
    Classify the document and produce a summary via an LLM call.
    Mutates and returns the payload.
    """
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

    # Truncate to avoid token overflow; 6 000 chars ≈ 1 500 tokens
    truncated_text = payload.raw_text[:6000]

    chain = CLASSIFY_PROMPT | llm
    response = chain.invoke({"text": truncated_text})

    # Parse the JSON response
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        # Attempt to extract JSON from markdown-fenced response
        import re
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = {
                "doc_type": "other",
                "summary": response.content[:500],
                "sections": [],
                "confidence": 0.0,
            }

    payload.doc_type = data.get("doc_type", "other")
    payload.doc_summary = data.get("summary", "")
    payload.metadata["sections"] = data.get("sections", [])
    payload.metadata["classification_confidence"] = data.get("confidence", 0.0)

    print(
        f"[Understanding] ✔ Classified as '{payload.doc_type}' "
        f"(confidence: {payload.metadata.get('classification_confidence', 'N/A')})"
    )
    return payload
