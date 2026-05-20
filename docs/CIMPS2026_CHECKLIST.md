# CIMPS2026 Audit Checklist

## Documentary Layer

- [ ] Verify MIHM PDF is present in `data/raw/`.
- [ ] Verify SHA-256 in `outputs/hash_ledger.json`.
- [ ] Verify `outputs/audit_report.md`.
- [ ] Verify required MIHM fields are detected.
- [ ] Verify absent fields are declared under ethics_of_silence.

## Runtime Layer

- [ ] Run `python run_full_audit.py --input "data/raw/MIHM_IEE.pdf"`.
- [ ] Confirm `outputs/audit_report.json` is generated.
- [ ] Confirm `outputs/audit_report.md` is generated.
- [ ] Confirm `outputs/hash_ledger.json` is generated.

## Observability Layer

- [ ] Run `python -m core.world_cli`.
- [ ] Confirm WSI and NTI are emitted.
- [ ] Confirm degraded sources are declared if any external feed fails.
- [ ] Run `python core/montecarlo.py`.
- [ ] Confirm Monte Carlo emits best/worst contextual windows.
- [ ] Run `python run_observability_audit.py --audio "data/audio/rem618.wav" --nti 0.5`.
- [ ] Confirm `audio_extraction.status = OK`.
- [ ] Confirm `R_sem` and `C_sem` remain null when no lyrics are provided.

## Container Layer

- [ ] Run `docker compose config`.
- [ ] Run `docker compose up --build`.
- [ ] Verify services:
  - `http://localhost:8000/docs`
  - `http://localhost:8001/docs`
  - `http://localhost:8002/docs`
  - `http://localhost:8003/docs`

## Classification

Final finding must be one of:

- ACCEPTED
- ACCEPTED_WITH_OBSERVATIONS
- NOT_REPRODUCIBLE
- INSUFFICIENT_TRACEABILITY