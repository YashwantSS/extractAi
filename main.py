"""
Document Intelligence Pipeline — Main Orchestrator
====================================================
Chains all pipeline stages together:
  Ingestion → Parsing → Understanding → Extraction → Validation → Analysis

Usage:
    python main.py <path-to-document>
    python main.py samples/invoice.pdf

The final output (JSON) is printed to stdout and saved to the output/ directory.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from config import settings
from pipeline.ingestion import ingest, IngestionError
from pipeline.parser import parse
from pipeline.understanding import understand
from pipeline.extraction import extract
from pipeline.validation import validate
from pipeline.analysis import analyze


def run_pipeline(file_path: str, save_output: bool = True) -> dict:
    """
    Execute the full document intelligence pipeline on a single file.

    Parameters
    ----------
    file_path : str
        Path to the input document.
    save_output : bool
        Whether to save the JSON result to the output directory.

    Returns
    -------
    dict
        Complete pipeline result including extracted data, validation, and analysis.
    """
    print("=" * 60)
    print("  DOCUMENT INTELLIGENCE PIPELINE")
    print("=" * 60)

    # ---- Stage 1: Ingestion ----
    print("\n▶ Stage 1/6: Ingestion")
    payload = ingest(file_path)

    # ---- Stage 2: Parsing ----
    print("\n▶ Stage 2/6: Parsing")
    payload = parse(payload)

    # ---- Stage 3: Understanding ----
    print("\n▶ Stage 3/6: Understanding (LLM Classification)")
    payload = understand(payload)

    # ---- Stage 4: Extraction ----
    print("\n▶ Stage 4/6: Structured Extraction")
    payload = extract(payload)

    # ---- Stage 5: Validation ----
    print("\n▶ Stage 5/6: Validation")
    payload = validate(payload)

    # ---- Stage 6: Analysis ----
    print("\n▶ Stage 6/6: Analysis")
    payload = analyze(payload)

    # ---- Build output ----
    result = {
        "pipeline_version": "1.0.0",
        "processed_at": datetime.now().isoformat(),
        "file": {
            "name": payload.file_name,
            "path": payload.file_path,
            "extension": payload.file_extension,
            "mime_type": payload.mime_type,
            "size_bytes": payload.file_size_bytes,
        },
        "classification": {
            "doc_type": payload.doc_type,
            "confidence": payload.metadata.get("classification_confidence", None),
            "sections": payload.metadata.get("sections", []),
        },
        "summary": payload.doc_summary,
        "extracted_data": payload.extracted_data,
        "validation": {
            "is_valid": len(payload.validation_errors) == 0,
            "errors": payload.validation_errors,
            "warnings": payload.validation_warnings,
        },
        "analysis": payload.analysis,
    }

    # ---- Print summary ----
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Document : {payload.file_name}")
    print(f"  Type     : {payload.doc_type}")
    print(f"  Valid    : {'Yes' if not payload.validation_errors else 'No'}")
    print(f"  Errors   : {len(payload.validation_errors)}")
    print(f"  Warnings : {len(payload.validation_warnings)}")
    print(f"  Risk     : {payload.analysis.get('risk_level', 'N/A')}")
    print("=" * 60)

    # ---- Save output ----
    if save_output:
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(file_path).stem
        out_path = os.path.join(settings.OUTPUT_DIR, f"{stem}_{timestamp}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Output saved to: {out_path}")

    return result


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-document>")
        print("Example: python main.py samples/invoice.pdf")
        sys.exit(1)

    file_path = sys.argv[1]

    # Validate config
    config_errors = settings.validate()
    if config_errors:
        print("Configuration errors:")
        for err in config_errors:
            print(f"  ✘ {err}")
        sys.exit(1)

    try:
        result = run_pipeline(file_path)
        # Print JSON to stdout
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(result, indent=2, default=str))
    except IngestionError as e:
        print(f"\n[Error] Ingestion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
