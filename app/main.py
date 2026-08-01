import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from app.models import Certificate
from app.thumbnails import ensure_thumbnail
from app.security import TokenGateMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
CERT_DIR = BASE_DIR / "certificates"
METADATA_PATH = BASE_DIR / "metadata.json"

app = FastAPI(
    title="Certificate Register",
    description="A REST API + recruiter-friendly view of my certifications.",
    version="1.0.0",
)

app.add_middleware(TokenGateMiddleware)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def load_certificates() -> list[Certificate]:
    if not METADATA_PATH.exists():
        return []
    raw = json.loads(METADATA_PATH.read_text())
    certs = [Certificate(**entry) for entry in raw]
    # newest first
    certs.sort(key=lambda c: c.date, reverse=True)
    return certs


def get_certificate_or_404(cert_id: str) -> Certificate:
    for c in load_certificates():
        if c.id == cert_id:
            return c
    raise HTTPException(status_code=404, detail=f"No certificate with id '{cert_id}'")


# ---------- REST API ----------

@app.get("/api/certificates", response_model=list[Certificate], tags=["certificates"])
def list_certificates(category: str | None = None):
    """List all certificates, optionally filtered by category."""
    certs = load_certificates()
    if category:
        certs = [c for c in certs if c.category.lower() == category.lower()]
    return certs


@app.get("/api/certificates/{cert_id}", response_model=Certificate, tags=["certificates"])
def get_certificate(cert_id: str):
    return get_certificate_or_404(cert_id)


@app.get("/api/certificates/{cert_id}/pdf", tags=["certificates"])
def get_certificate_pdf(cert_id: str):
    cert = get_certificate_or_404(cert_id)
    pdf_path = CERT_DIR / cert.filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing on server")
    return FileResponse(pdf_path, media_type="application/pdf", filename=cert.filename)


@app.get("/api/certificates/{cert_id}/thumbnail", tags=["certificates"])
def get_certificate_thumbnail(cert_id: str):
    cert = get_certificate_or_404(cert_id)
    pdf_path = CERT_DIR / cert.filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing on server")
    thumb_path = ensure_thumbnail(pdf_path)
    return FileResponse(thumb_path, media_type="image/png")


@app.get("/api/categories", tags=["certificates"])
def list_categories():
    return sorted({c.category for c in load_certificates()})


# ---------- Recruiter-facing HTML view ----------

@app.get("/", response_class=HTMLResponse, tags=["view"])
def view_register(request: Request):
    certs = load_certificates()
    categories = sorted({c.category for c in certs})
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "certificates": certs, "categories": categories},
    )