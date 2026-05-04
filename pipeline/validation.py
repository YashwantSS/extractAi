"""
Validation Module
------------------
Runs Pydantic schema validation and custom business rules on the
extracted data. Returns errors and warnings in the payload.
"""
from __future__ import annotations

import re
from datetime import datetime

from pipeline.ingestion import DocumentPayload
from schemas.models import get_schema_for_doc_type


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(payload: DocumentPayload) -> DocumentPayload:
    """
    Validate extracted_data against the Pydantic schema and business rules.
    Populates payload.validation_errors and payload.validation_warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    data = payload.extracted_data
    if not data:
        errors.append("No data was extracted to validate.")
        payload.validation_errors = errors
        print("[Validation] ✘ No data to validate.")
        return payload

    # --- 1. Schema validation ---
    schema_cls = get_schema_for_doc_type(payload.doc_type)
    try:
        schema_cls.model_validate(data)
    except Exception as e:
        errors.append(f"Schema validation error: {e}")

    # --- 2. Business rules (per doc type) ---
    rule_fn = BUSINESS_RULES.get(payload.doc_type)
    if rule_fn:
        rule_errors, rule_warnings = rule_fn(data)
        errors.extend(rule_errors)
        warnings.extend(rule_warnings)

    # --- 3. Generic rules ---
    gen_errors, gen_warnings = _generic_rules(data)
    errors.extend(gen_errors)
    warnings.extend(gen_warnings)

    payload.validation_errors.extend(errors)
    payload.validation_warnings.extend(warnings)

    status = "✔" if not errors else "✘"
    print(
        f"[Validation] {status} {len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return payload


# ---------------------------------------------------------------------------
# Generic rules (apply to all doc types)
# ---------------------------------------------------------------------------

def _generic_rules(data: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    # Check date formats
    for key, value in data.items():
        if isinstance(value, str) and "date" in key.lower() and value:
            if not _is_valid_date(value):
                warnings.append(
                    f"Field '{key}' has value '{value}' — expected YYYY-MM-DD format."
                )

    return errors, warnings


def _is_valid_date(value: str) -> bool:
    """Check if a string is a valid YYYY-MM-DD date."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Invoice-specific rules
# ---------------------------------------------------------------------------

def _validate_invoice(data: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    # Required fields
    for field in ["invoice_number", "vendor_name", "total_amount"]:
        if not data.get(field):
            warnings.append(f"Invoice is missing recommended field: '{field}'")

    # Total vs line items
    line_items = data.get("line_items", [])
    total = data.get("total_amount")
    if line_items and total is not None:
        computed_sum = sum(
            item.get("amount", 0) or 0 for item in line_items
        )
        if computed_sum > 0 and abs(computed_sum - total) > 0.01:
            subtotal = data.get("subtotal")
            tax = data.get("tax_amount", 0) or 0
            # Allow if subtotal + tax ≈ total
            if subtotal is not None and abs(subtotal + tax - total) < 0.02:
                pass  # OK, total = subtotal + tax
            else:
                warnings.append(
                    f"Line item sum ({computed_sum:.2f}) does not match "
                    f"total_amount ({total:.2f}). Verify tax/discount."
                )

    # Amount should be positive
    if total is not None and total < 0:
        errors.append(f"total_amount is negative ({total}). Likely an extraction error.")

    return errors, warnings


# ---------------------------------------------------------------------------
# Receipt-specific rules
# ---------------------------------------------------------------------------

def _validate_receipt(data: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    total = data.get("total")
    if total is not None and total < 0:
        errors.append(f"Receipt total is negative ({total}).")

    items = data.get("items", [])
    if not items:
        warnings.append("No items extracted from receipt.")

    return errors, warnings


# ---------------------------------------------------------------------------
# Contract-specific rules
# ---------------------------------------------------------------------------

def _validate_contract(data: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    parties = data.get("parties", [])
    if len(parties) < 2:
        warnings.append("A contract typically has at least 2 parties.")

    effective = data.get("effective_date")
    expiration = data.get("expiration_date")
    if effective and expiration and _is_valid_date(effective) and _is_valid_date(expiration):
        if expiration < effective:
            errors.append("Expiration date is before effective date.")

    return errors, warnings


# ---------------------------------------------------------------------------
# Bank Statement rules
# ---------------------------------------------------------------------------

def _validate_bank_statement(data: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []

    opening = data.get("opening_balance")
    closing = data.get("closing_balance")
    transactions = data.get("transactions", [])

    if opening is not None and closing is not None and transactions:
        net = sum(t.get("amount", 0) or 0 for t in transactions)
        expected_closing = opening + net
        if abs(expected_closing - closing) > 0.02:
            warnings.append(
                f"Opening ({opening}) + net transactions ({net:.2f}) = "
                f"{expected_closing:.2f}, but closing balance is {closing}. "
                "Possible missing transactions."
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

BUSINESS_RULES: dict = {
    "invoice": _validate_invoice,
    "receipt": _validate_receipt,
    "contract": _validate_contract,
    "bank_statement": _validate_bank_statement,
}
