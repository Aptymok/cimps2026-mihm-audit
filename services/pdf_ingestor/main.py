from fastapi import FastAPI, UploadFile
from pypdf import PdfReader
import io

app = FastAPI(title="MIHM PDF Ingestor")

@app.get("/")
def root():
    return {"status": "online"}

@app.post("/ingest")
async def ingest_pdf(file: UploadFile):
    content = await file.read()

    pdf = PdfReader(io.BytesIO(content))

    pages = []

    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        pages.append({
            "page": i,
            "characters": len(text),
            "preview": text[:500]
        })

    return {
        "filename": file.filename,
        "pages": len(pages),
        "content": pages
    }