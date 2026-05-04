"""
Pydantic schemas for structured extraction.
Each schema corresponds to a document type.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    description: str = Field(..., description="Description of the line item")
    quantity: Optional[float] = Field(None, description="Quantity")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    amount: Optional[float] = Field(None, description="Total amount for this line")


class InvoiceSchema(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Invoice number/ID")
    invoice_date: Optional[str] = Field(None, description="Date of the invoice (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Payment due date (YYYY-MM-DD)")
    vendor_name: Optional[str] = Field(None, description="Name of the vendor/seller")
    vendor_address: Optional[str] = Field(None, description="Address of the vendor")
    customer_name: Optional[str] = Field(None, description="Name of the customer/buyer")
    customer_address: Optional[str] = Field(None, description="Address of the customer")
    line_items: list[LineItem] = Field(default_factory=list, description="List of line items")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    total_amount: Optional[float] = Field(None, description="Total payable amount")
    currency: Optional[str] = Field("USD", description="Currency code")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")


# ---------------------------------------------------------------------------
# Receipt
# ---------------------------------------------------------------------------

class ReceiptItem(BaseModel):
    item_name: str = Field(..., description="Name of the purchased item")
    quantity: Optional[float] = Field(None)
    price: Optional[float] = Field(None)


class ReceiptSchema(BaseModel):
    store_name: Optional[str] = Field(None, description="Name of the store/merchant")
    store_address: Optional[str] = Field(None)
    receipt_date: Optional[str] = Field(None, description="Date of purchase (YYYY-MM-DD)")
    items: list[ReceiptItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    currency: Optional[str] = Field("USD")


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class ContractSchema(BaseModel):
    contract_title: Optional[str] = Field(None)
    parties: list[str] = Field(default_factory=list, description="Names of parties involved")
    effective_date: Optional[str] = Field(None)
    expiration_date: Optional[str] = Field(None)
    contract_value: Optional[float] = Field(None, description="Monetary value of the contract")
    currency: Optional[str] = Field("USD")
    key_terms: list[str] = Field(default_factory=list, description="Key clauses/terms extracted")
    governing_law: Optional[str] = Field(None, description="Jurisdiction / governing law")
    signatures: list[str] = Field(default_factory=list, description="Signatory names")
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Report / Generic
# ---------------------------------------------------------------------------

class ReportSchema(BaseModel):
    title: Optional[str] = Field(None)
    author: Optional[str] = Field(None)
    date: Optional[str] = Field(None)
    sections: list[str] = Field(default_factory=list, description="Section headings found")
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Bank Statement
# ---------------------------------------------------------------------------

class Transaction(BaseModel):
    date: Optional[str] = None
    description: str = ""
    amount: Optional[float] = None
    transaction_type: Optional[str] = Field(None, description="debit or credit")


class BankStatementSchema(BaseModel):
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    statement_period: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    transactions: list[Transaction] = Field(default_factory=list)
    currency: Optional[str] = Field("USD")


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

class ResumeSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list, description="Job titles / companies")
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Generic / Fallback
# ---------------------------------------------------------------------------

class GenericSchema(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None
    key_fields: dict = Field(default_factory=dict, description="Arbitrary key-value pairs")
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Registry: doc_type → schema class
# ---------------------------------------------------------------------------

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "invoice": InvoiceSchema,
    "receipt": ReceiptSchema,
    "contract": ContractSchema,
    "report": ReportSchema,
    "bank_statement": BankStatementSchema,
    "resume": ResumeSchema,
    "letter": GenericSchema,
    "form": GenericSchema,
    "medical_record": GenericSchema,
    "other": GenericSchema,
}


def get_schema_for_doc_type(doc_type: str) -> type[BaseModel]:
    """Return the Pydantic model class for a given document type."""
    return SCHEMA_REGISTRY.get(doc_type, GenericSchema)
