"""
Analysis Module
----------------
Generates insights, summaries, anomaly flags, and statistics
from the validated extracted data using an LLM + pandas.
"""
from __future__ import annotations

import json

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from pipeline.ingestion import DocumentPayload


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

ANALYZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert document analyst. Given the extracted structured data "
            "and the original document summary, produce a comprehensive analysis.\n\n"
            "Return a JSON object with:\n"
            '  "insights": [list of key insights / observations],\n'
            '  "anomalies": [list of any anomalies or red flags detected],\n'
            '  "statistics": {{key: value}} dict of computed statistics where applicable,\n'
            '  "recommendations": [list of actionable recommendations],\n'
            '  "risk_level": "low" | "medium" | "high" based on anomalies found.\n\n'
            "Return ONLY valid JSON, no markdown fences.",
        ),
        (
            "human",
            "Document type: {doc_type}\n\n"
            "Summary: {summary}\n\n"
            "Extracted data:\n{extracted_data}\n\n"
            "Validation errors: {errors}\n"
            "Validation warnings: {warnings}\n",
        ),
    ]
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze(payload: DocumentPayload) -> DocumentPayload:
    """
    Run LLM-powered analysis + basic statistical analysis on the payload.
    Populates ``payload.analysis``.
    """
    analysis_result: dict = {}

    # --- Statistical analysis (for docs with numeric data) ---
    stats = _compute_statistics(payload)
    if stats:
        analysis_result["computed_statistics"] = stats

    # --- LLM analysis ---
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

    chain = ANALYZE_PROMPT | llm
    response = chain.invoke(
        {
            "doc_type": payload.doc_type,
            "summary": payload.doc_summary,
            "extracted_data": json.dumps(payload.extracted_data, indent=2, default=str),
            "errors": json.dumps(payload.validation_errors),
            "warnings": json.dumps(payload.validation_warnings),
        }
    )

    # Parse LLM response
    try:
        llm_analysis = json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if match:
            try:
                llm_analysis = json.loads(match.group())
            except json.JSONDecodeError:
                llm_analysis = {"raw_analysis": response.content}
        else:
            llm_analysis = {"raw_analysis": response.content}

    analysis_result.update(llm_analysis)
    payload.analysis = analysis_result

    insight_count = len(analysis_result.get("insights", []))
    anomaly_count = len(analysis_result.get("anomalies", []))
    risk = analysis_result.get("risk_level", "unknown")
    print(
        f"[Analysis] ✔ {insight_count} insight(s), {anomaly_count} anomaly(ies), "
        f"risk: {risk}"
    )
    return payload


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def _compute_statistics(payload: DocumentPayload) -> dict:
    """Compute basic statistics from tables or extracted numeric data."""
    stats = {}

    # From tables
    if payload.tables:
        for i, table in enumerate(payload.tables):
            try:
                df = pd.DataFrame(table[1:], columns=table[0])
                numeric_cols = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
                if not numeric_cols.empty:
                    desc = numeric_cols.describe().to_dict()
                    stats[f"table_{i + 1}"] = {
                        col: {k: round(v, 2) for k, v in col_stats.items()}
                        for col, col_stats in desc.items()
                    }
            except Exception:
                continue

    # From extracted line items (invoices)
    line_items = payload.extracted_data.get("line_items", [])
    if line_items:
        amounts = [
            item.get("amount", 0) or 0
            for item in line_items
            if isinstance(item, dict)
        ]
        if amounts:
            stats["line_items"] = {
                "count": len(amounts),
                "total": round(sum(amounts), 2),
                "average": round(sum(amounts) / len(amounts), 2),
                "min": round(min(amounts), 2),
                "max": round(max(amounts), 2),
            }

    # From transactions (bank statements)
    transactions = payload.extracted_data.get("transactions", [])
    if transactions:
        tx_amounts = [
            t.get("amount", 0) or 0
            for t in transactions
            if isinstance(t, dict)
        ]
        if tx_amounts:
            credits = [a for a in tx_amounts if a > 0]
            debits = [a for a in tx_amounts if a < 0]
            stats["transactions"] = {
                "count": len(tx_amounts),
                "total_credits": round(sum(credits), 2),
                "total_debits": round(sum(debits), 2),
                "net": round(sum(tx_amounts), 2),
            }

    return stats
