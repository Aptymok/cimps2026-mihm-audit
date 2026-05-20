## Execution Modes

### Mode A — GitHub Actions / Recommended

This is the canonical reproducible execution mode.

Every push to `main` runs:

python run_full_audit.py --input "data/raw/MIHM_IEE.pdf"

### Mode B — Local Python

Use when Docker is not available.
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_full_audit.py --input "data/raw/MIHM_IEE.pdf"

### Mode C — Docker Compose / Optional

Docker Compose is supported only when the local organization allows Docker Desktop networking and container bridge interfaces.

docker compose up --build

```bash