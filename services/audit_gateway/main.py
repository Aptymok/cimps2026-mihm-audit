from fastapi import FastAPI, UploadFile
from pypdf import PdfReader
import io
import re
import hashlib
from datetime import datetime

app = FastAPI(title="MIHM Audit Gateway")

REQUIRED_FIELDS = [
    "MIHM",
    "NTI",
    "IHG",
    "Monte Carlo",
    "System Friction",
]

def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def extract_pdf_text(content: bytes) -> str:
    pdf = PdfReader(io.BytesIO(content))
    pages = []

    for page in pdf.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n".join(pages)

def validate_metadata(text: str) -> dict:
    found = {}
    missing = []

    for field in REQUIRED_FIELDS:
        exists = field.lower() in text.lower()
        found[field] = exists

        if not exists:
            missing.append(field)

    version_match = re.search(r"v\d+\.\d+", text)

    return {
        "auditability": len(missing) < 3,
        "fields_detected": found,
        "missing_fields": missing,
        "version_detected": version_match.group(0) if version_match else None,
        "ethics_of_silence": [
            {
                "field": field,
                "value": None,
                "reason": "Campo no detectable en documento."
            }
            for field in missing
        ],
    }

@app.get("/")
def root():
    return {
        "status": "audit_gateway_online",
        "pipeline": "PDF -> extraction -> metadata_validation -> hash_ledger"
    }

@app.post("/audit")
async def audit_pdf(file: UploadFile):
    content = await file.read()

    text = extract_pdf_text(content)
    metadata_report = validate_metadata(text)

    return {
        "audit_id": f"MIHM-CIMPS2026-{datetime.utcnow().isoformat()}",
        "filename": file.filename,
        "sha256": sha256_bytes(content),
        "characters_extracted": len(text),
        "metadata_validation": metadata_report,
        "operational_status": (
            "AUDITABLE"
            if metadata_report["auditability"]
            else "INSUFFICIENT_EVIDENCE"
        )
    }