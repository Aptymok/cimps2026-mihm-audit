# CIMPS2026 Presentation Protocol — MIHM v3.0

## 1. Nature of the Submission

This repository presents MIHM v3.0 as an executable observability prototype.

It does not claim to certify aesthetic value, commercial success, or absolute scientific truth.

It demonstrates that a musical work and its technical document can be processed through a reproducible audit pipeline.

## 2. Executable Layers

### Layer 1 — Documentary Audit

Command:

```bash
python run_full_audit.py --input "data/raw/MIHM_IEE.pdf"
```

Output:
outputs/observability_report.json

If audio is absent, the system declares NOT_EXECUTED.

## 3. Ethics of Silence

Variables that cannot be measured are not inferred.

Missing sources, absent audio, unavailable text, failed external feeds, or non-measurable variables are declared explicitly.

## 4. Reproducibility

The canonical validation environment is GitHub Actions.

Docker Compose is available for local microservice execution.

## 5. Validity Boundary

This prototype validates:

processability
traceability
reproducibility
source degradation handling
minimum MIHM vector emission
contextual simulation
acoustic feature extraction

It does not validate:

aesthetic superiority
commercial prediction
absolute scientific truth
cultural interpretation