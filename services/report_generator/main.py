from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

app = FastAPI(title="MIHM Report Generator")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


class EthicsItem(BaseModel):
    field: str
    value: Optional[Any] = None
    reason: str


class MetadataValidation(BaseModel):
    auditability: bool
    fields_detected: Dict[str, bool]
    missing_fields: List[str]
    version_detected: Optional[str] = None
    ethics_of_silence: List[EthicsItem]


class AuditPayload(BaseModel):
    audit_id: str
    filename: str
    sha256: str
    characters_extracted: int
    metadata_validation: MetadataValidation
    operational_status: str


def build_markdown_report(payload: AuditPayload) -> str:
    detected_lines = "\n".join(
        f"- {field}: {'OK' if present else 'MISSING'}"
        for field, present in payload.metadata_validation.fields_detected.items()
    )

    missing_lines = "\n".join(
        f"- {field}"
        for field in payload.metadata_validation.missing_fields
    ) or "- None"

    silence_lines = "\n".join(
        f"- {item.field}: {item.reason}"
        for item in payload.metadata_validation.ethics_of_silence
    ) or "- None"

    return f"""# MIHM CIMPS2026 Audit Report

## Audit Identity

- Audit ID: `{payload.audit_id}`
- File: `{payload.filename}`
- SHA-256: `{payload.sha256}`

## Operational Status

**{payload.operational_status}**

## Extraction

- Characters extracted: `{payload.characters_extracted}`

## Metadata Validation

- Auditability: `{payload.metadata_validation.auditability}`
- Version detected: `{payload.metadata_validation.version_detected}`

## Required Fields

{detected_lines}

## Missing Fields

{missing_lines}

## Ethics of Silence

{silence_lines}

## Technical Note

This report does not certify scientific truth. It certifies minimum documentary traceability, reproducibility signals, and detectable audit fields.

Generated automatically by System Friction / MIHM CIMPS2026 audit pipeline.
"""


@app.get("/")
def root():
    return {
        "status": "report_generator_online",
        "outputs": [
            "outputs/audit_report.json",
            "outputs/audit_report.md",
            "outputs/hash_ledger.json"
        ]
    }


@app.post("/generate")
def generate_report(payload: AuditPayload):
    report_json_path = OUTPUT_DIR / "audit_report.json"
    report_md_path = OUTPUT_DIR / "audit_report.md"
    ledger_path = OUTPUT_DIR / "hash_ledger.json"

    payload_dict = payload.model_dump()

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(payload_dict, f, indent=2, ensure_ascii=False)

    markdown = build_markdown_report(payload)

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    ledger = {
        "audit_id": payload.audit_id,
        "filename": payload.filename,
        "sha256": payload.sha256,
        "generated_at": datetime.utcnow().isoformat(),
        "status": payload.operational_status
    }

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

    return {
        "status": "REPORT_GENERATED",
        "files": {
            "json": str(report_json_path),
            "markdown": str(report_md_path),
            "ledger": str(ledger_path)
        }
    }
