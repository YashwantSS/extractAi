# 📄 Document Intelligence Pipeline

An AI-powered pipeline that ingests **any document type**, understands its content, extracts structured data, validates it against business rules, and generates actionable analysis — all in a single command.

---

## 🏗️ Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐
│ Ingestion│───▶│ Parsing  │───▶│Understanding │───▶│ Extraction │───▶│ Validation │───▶│ Analysis │
│          │    │  & OCR   │    │  (LLM)       │    │  (LLM +    │    │ (Pydantic  │    │ (LLM +   │
│ File I/O │    │ Text +   │    │ Classify &   │    │  Pydantic) │    │  + Rules)  │    │  pandas) │
│ Validate │    │ Tables   │    │ Summarize    │    │  Schemas   │    │  Business  │    │ Insights │
└──────────┘    └──────────┘    └──────────────┘    └────────────┘    └────────────┘    └──────────┘
```

### Pipeline Stages

| # | Stage | Description |
|---|---|---|
| 1 | **Ingestion** | Accepts the file, validates type/size, creates a `DocumentPayload` |
| 2 | **Parsing** | Extracts raw text and tables using format-specific parsers (OCR for scanned docs) |
| 3 | **Understanding** | LLM classifies document type (invoice, contract, receipt, etc.) and summarizes content |
| 4 | **Extraction** | LLM extracts structured fields into a typed Pydantic schema matched to the doc type |
| 5 | **Validation** | Pydantic schema validation + custom business rules (totals match, dates valid, etc.) |
| 6 | **Analysis** | LLM + pandas generate insights, flag anomalies, compute statistics, assess risk |

---

## 📁 Project Structure

```
agenticAI/
├── main.py                    # CLI entry point & pipeline orchestrator
├── config.py                  # Settings loaded from .env
├── requirements.txt           # Python dependencies
├── .env.example               # Template for environment variables
├── .gitignore
│
├── pipeline/                  # Core pipeline modules
│   ├── __init__.py
│   ├── ingestion.py           # File validation & payload creation
│   ├── parser.py              # Text/table extraction (PDF, DOCX, images, etc.)
│   ├── understanding.py       # LLM document classification & summarization
│   ├── extraction.py          # LLM structured data extraction
│   ├── validation.py          # Schema + business rule validation
│   └── analysis.py            # LLM insights + statistical analysis
│
├── schemas/                   # Pydantic models for each document type
│   ├── __init__.py
│   └── models.py              # Invoice, Receipt, Contract, Report, Resume, etc.
│
├── samples/                   # Sample test documents
│   ├── sample_invoice.txt
│   └── sample_receipt.csv
│
├── prompts/                   # (Reserved) Prompt templates
└── output/                    # Pipeline JSON output files
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Core runtime |
| **LLM Framework** | LangChain | Prompt chaining, output parsing |
| **LLM Provider** | OpenAI GPT-4o | Document understanding, extraction, analysis |
| **Schema/Validation** | Pydantic v2 | Type-safe structured output + validators |
| **PDF Parsing** | PyMuPDF (fitz) | Fast PDF text + table extraction |
| **OCR** | Tesseract (pytesseract) | Scanned document / image text extraction |
| **Word Docs** | python-docx | DOCX parsing |
| **Excel** | openpyxl | XLSX parsing |
| **HTML** | BeautifulSoup4 | HTML text extraction |
| **Data Analysis** | pandas | Statistical analysis on extracted data |
| **Config** | python-dotenv | Environment variable management |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+** installed
- **Tesseract OCR** (for scanned documents / images):
  ```bash
  # macOS
  brew install tesseract

  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr

  # Windows — download installer from https://github.com/tesseract-ocr/tesseract
  ```
- **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys))

### 2. Installation

```bash
# Clone / navigate to the project
cd extractAi

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```
# Install Tesseract OCR (needed for scanned docs/images)
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows — download from https://github.com/tesseract-ocr/tesseract


### 3. Configuration

```bash
# Create your .env file from the template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 4. Run the Pipeline

```bash
# Process a document
python main.py <path-to-document>

# Examples:
python main.py samples/sample_invoice.txt
python main.py samples/sample_receipt.csv
python main.py /path/to/your/document.pdf
python main.py /path/to/scanned_image.png
```

---

## 📋 Supported Document Types

### Input Formats
| Format | Extensions | Parser Used |
|---|---|---|
| PDF | `.pdf` | PyMuPDF + OCR fallback |
| Images | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` | Tesseract OCR |
| Word | `.docx` | python-docx |
| Excel | `.xlsx` | openpyxl |
| CSV | `.csv` | Python csv module |
| HTML | `.html` | BeautifulSoup |
| Plain Text | `.txt`, `.md` | Direct read |

### Document Classifications
The LLM automatically classifies documents into these categories, each with a dedicated Pydantic schema:

| Type | Schema | Key Fields Extracted |
|---|---|---|
| **Invoice** | `InvoiceSchema` | Invoice #, dates, vendor/customer, line items, totals, tax |
| **Receipt** | `ReceiptSchema` | Store, date, items, subtotal, tax, total, payment method |
| **Contract** | `ContractSchema` | Parties, dates, value, key terms, governing law, signatures |
| **Report** | `ReportSchema` | Title, author, sections, findings, recommendations |
| **Bank Statement** | `BankStatementSchema` | Bank, account, balances, transactions |
| **Resume** | `ResumeSchema` | Name, contact, skills, experience, education |
| **Generic** | `GenericSchema` | Title, date, author, arbitrary key-value pairs |

---

## 📤 Output Format

The pipeline produces a JSON file saved to `output/` with this structure:

```json
{
  "pipeline_version": "1.0.0",
  "processed_at": "2026-05-04T10:30:00",
  "file": {
    "name": "invoice.pdf",
    "extension": ".pdf",
    "mime_type": "application/pdf",
    "size_bytes": 45230
  },
  "classification": {
    "doc_type": "invoice",
    "confidence": 0.95,
    "sections": ["header", "line_items", "totals", "payment_info"]
  },
  "summary": "Invoice #INV-2026-0042 from Acme Solutions to TechCorp for cloud services totaling $8,083.25, due May 15, 2026.",
  "extracted_data": {
    "invoice_number": "INV-2026-0042",
    "invoice_date": "2026-04-15",
    "vendor_name": "Acme Solutions Inc.",
    "total_amount": 8083.25,
    "line_items": [...]
  },
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "analysis": {
    "insights": ["Largest line item is Cloud Hosting at $2,500"],
    "anomalies": [],
    "statistics": {"line_items": {"count": 4, "total": 7450.0}},
    "recommendations": ["Verify tax rate matches local requirements"],
    "risk_level": "low"
  }
}
```

---

## ✅ Validation Rules

### Schema Validation (All Documents)
- Field type enforcement via Pydantic v2
- Date format validation (YYYY-MM-DD)
- Required vs. optional field checks

### Business Rules (Per Document Type)

| Document Type | Rules Applied |
|---|---|
| **Invoice** | Line item sum ≈ total; positive amounts; required fields (invoice #, vendor, total) |
| **Receipt** | Positive total; items extracted |
| **Contract** | ≥ 2 parties; expiration after effective date |
| **Bank Statement** | Opening balance + transactions ≈ closing balance |

---

## 🔧 Configuration Options

All settings in `.env`:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | LLM model to use |
| `OPENAI_TEMPERATURE` | `0.0` | LLM temperature (0 = deterministic) |
| `TESSERACT_CMD` | `tesseract` | Path to Tesseract binary |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size allowed |
| `OUTPUT_DIR` | `output` | Directory for JSON output files |

---

## 🧩 Extending the Pipeline

### Adding a New Document Type

1. **Create a Pydantic schema** in `schemas/models.py`:
   ```python
   class InsuranceClaimSchema(BaseModel):
       claim_number: Optional[str] = None
       policy_number: Optional[str] = None
       claimant_name: Optional[str] = None
       incident_date: Optional[str] = None
       claim_amount: Optional[float] = None
       description: Optional[str] = None
   ```

2. **Register it** in `SCHEMA_REGISTRY`:
   ```python
   SCHEMA_REGISTRY["insurance_claim"] = InsuranceClaimSchema
   ```

3. **Add business rules** in `pipeline/validation.py`:
   ```python
   def _validate_insurance_claim(data: dict):
       errors, warnings = [], []
       if not data.get("claim_number"):
           errors.append("Missing claim number")
       return errors, warnings

   BUSINESS_RULES["insurance_claim"] = _validate_insurance_claim
   ```

4. **Update the classification prompt** in `pipeline/understanding.py` to include `"insurance_claim"` in the doc_type list.

### Swapping LLM Providers

Replace `ChatOpenAI` with any LangChain-compatible model:

```python
# Anthropic Claude
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# Local Ollama
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3")

# Azure OpenAI
from langchain_openai import AzureChatOpenAI
llm = AzureChatOpenAI(deployment_name="gpt-4o", ...)
```

---

## 🧪 Testing

```bash
# Test with the included sample files
python main.py samples/sample_invoice.txt
python main.py samples/sample_receipt.csv

# Test with your own documents
python main.py /path/to/your/document.pdf
```

---

## 📊 Example Run

```
============================================================
  DOCUMENT INTELLIGENCE PIPELINE
============================================================

▶ Stage 1/6: Ingestion
[Ingestion] ✔ Accepted 'sample_invoice.txt' (.txt, 1.2 KB)

▶ Stage 2/6: Parsing
[Parser] ✔ Extracted 1,247 chars of text, 0 table(s)

▶ Stage 3/6: Understanding (LLM Classification)
[Understanding] ✔ Classified as 'invoice' (confidence: 0.98)

▶ Stage 4/6: Structured Extraction
[Extraction] ✔ Extracted 12 populated fields for 'invoice'

▶ Stage 5/6: Validation
[Validation] ✔ 0 error(s), 0 warning(s)

▶ Stage 6/6: Analysis
[Analysis] ✔ 3 insight(s), 0 anomaly(ies), risk: low

============================================================
  PIPELINE COMPLETE
============================================================
  Document : sample_invoice.txt
  Type     : invoice
  Valid    : Yes
  Errors   : 0
  Warnings : 0
  Risk     : low
============================================================
```

---

