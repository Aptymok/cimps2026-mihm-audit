from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import re

app = FastAPI(title="MIHM Metadata Validator")

class DocumentPayload(BaseModel):
    text: str

REQUIRED_FIELDS = [
    "MIHM",
    "NTI",
    "IHG",
    "Monte Carlo",
    "System Friction",
]

@app.get("/")
def root():
    return {"status": "validator_online"}

@app.post("/validate")
def validate_document(payload: DocumentPayload):

    text = payload.text

    found = {}
    missing = []

    for field in REQUIRED_FIELDS:
        exists = field.lower() in text.lower()
        found[field] = exists

        if not exists:
            missing.append(field)

    version_match = re.search(r'v\d+\.\d+', text)

    return {
        "auditability": len(missing) < 3,
        "fields_detected": found,
        "missing_fields": missing,
        "version_detected": version_match.group(0) if version_match else None,
        "ethics_of_silence": [
            {
                "field": m,
                "value": None,
                "reason": "Campo no detectable en documento."
            }
            for m in missing
        ]
    }