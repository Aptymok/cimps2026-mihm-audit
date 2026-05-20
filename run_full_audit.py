from pathlib import Path
from pypdf import PdfReader
import argparse
import hashlib
import json
import re
from datetime import datetime

OUTPUT_DIR = Path("outputs")

REQUIRED_FIELDS = [
    "MIHM",
    "NTI",
    "IHG",
    "Monte Carlo",
    "System Friction",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
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
        ]
    }


def build_markdown_report(report: dict) -> str:
    metadata = report["metadata_validation"]

    detected_lines = "\n".join(
        f"- {field}: {'OK' if present else 'MISSING'}"
        for field, present in metadata["fields_detected"].items()
    )

    missing_lines = "\n".join(
        f"- {field}" for field in metadata["missing_fields"]
    ) or "- None"

    silence_lines = "\n".join(
        f"- {item['field']}: {item['reason']}"
        for item in metadata["ethics_of_silence"]
    ) or "- None"

    return f"""# MIHM CIMPS2026 Audit Report

## Audit Identity

- Audit ID: `{report['audit_id']}`
- File: `{report['filename']}`
- SHA-256: `{report['sha256']}`
- Generated at: `{report['generated_at']}`

## Operational Status

**{report['operational_status']}**

## Extraction

- Characters extracted: `{report['characters_extracted']}`

## Metadata Validation

- Auditability: `{metadata['auditability']}`
- Version detected: `{metadata['version_detected']}`

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


def run_full_audit(input_path: Path, output_dir: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    text = extract_pdf_text(input_path)
    metadata = validate_metadata(text)
    generated_at = datetime.utcnow().isoformat()

    report = {
        "audit_id": f"MIHM-CIMPS2026-{generated_at}",
        "filename": input_path.name,
        "input_file": str(input_path),
        "sha256": sha256_file(input_path),
        "characters_extracted": len(text),
        "metadata_validation": metadata,
        "operational_status": "AUDITABLE" if metadata["auditability"] else "INSUFFICIENT_EVIDENCE",
        "generated_at": generated_at,
    }

    with open(output_dir / "audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    with open(output_dir / "audit_report.md", "w", encoding="utf-8") as f:
        f.write(build_markdown_report(report))

    ledger = {
        "audit_id": report["audit_id"],
        "filename": report["filename"],
        "input_file": report["input_file"],
        "sha256": report["sha256"],
        "generated_at": generated_at,
        "status": report["operational_status"]
    }

    with open(output_dir / "hash_ledger.json", "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

    return report


def main():
    parser = argparse.ArgumentParser(description="Run full MIHM CIMPS2026 audit pipeline.")
    parser.add_argument("--input", required=True, help="Path to input MIHM PDF")
    parser.add_argument("--output", default="outputs", help="Output directory")
    args = parser.parse_args()

    report = run_full_audit(Path(args.input), Path(args.output))
    print(json.dumps({
        "status": report["operational_status"],
        "audit_id": report["audit_id"],
        "outputs": [
            str(Path(args.output) / "audit_report.json"),
            str(Path(args.output) / "audit_report.md"),
            str(Path(args.output) / "hash_ledger.json"),
        ]
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
