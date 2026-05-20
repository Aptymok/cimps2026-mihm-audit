FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .

RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-docker.txt

COPY . .

CMD ["uvicorn", "services.audit_gateway.main:app", "--host", "0.0.0.0", "--port", "8002"]
