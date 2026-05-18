from pathlib import Path
from pypdf import PdfReader
import hashlib
import json
from datetime import datetime

INPUT_DEFAULT = "data/raw/MIHM_IEE (1).pdf"
OUTPUT_DIR = Path("outputs")

MIHM_VARIABLES = [
    "F_s", "G_f", "C_s", "R_sem", "C_sem", "Phi",
    "I_mc", "E_r", "V_i", "D_i", "D_cog"
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_pdf_text(path):
    reader = PdfReader(path)
    text = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        text.append({"page": i, "text": page_text})
    return text

def audit_document(path):
    pdf_path = Path(path)
    pages = extract_pdf_text(pdf_path)
    full_text = "\n".join(p["text"] for p in pages)

    detected_variables = {
        var: (var in full_text) for var in MIHM_VARIABLES
    }

    ethics_of_silence = []
    for var, found in detected_variables.items():
        if not found:
            ethics_of_silence.append({
                "variable": var,
                "value": None,
                "reason": "No se encontró evidencia textual suficiente en el PDF."
            })

    report = {
        "audit_id": f"MIHM-CIMPS2026-{datetime.utcnow().isoformat()}",
        "input_file": str(pdf_path),
        "sha256": sha256_file(pdf_path),
        "pages": len(pages),
        "mihm_variables_detected": detected_variables,
        "ethics_of_silence": ethics_of_silence,
        "status": "AUDITABLE" if len(ethics_of_silence) < len(MIHM_VARIABLES) else "INSUFFICIENT_EVIDENCE",
        "note": "Este reporte no valida verdad científica; valida trazabilidad documental mínima."
    }

    return report

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    report = audit_document(INPUT_DEFAULT)

    with open(OUTPUT_DIR / "audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "hash_ledger.json", "w", encoding="utf-8") as f:
        json.dump({
            "file": report["input_file"],
            "sha256": report["sha256"],
            "generated_at": report["audit_id"]
        }, f, indent=2, ensure_ascii=False)

    md = f"""# MIHM CIMPS2026 Audit Report

## Estado
{report["status"]}

## Archivo
{report["input_file"]}

## SHA-256
`{report["sha256"]}`

## Páginas
{report["pages"]}

## Variables MIHM detectadas
{json.dumps(report["mihm_variables_detected"], indent=2, ensure_ascii=False)}

## Ética del silencio
{json.dumps(report["ethics_of_silence"], indent=2, ensure_ascii=False)}

## Nota
{report["note"]}
"""

    with open(OUTPUT_DIR / "audit_report.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("Auditoría generada en outputs/")

if __name__ == "__main__":
    main()