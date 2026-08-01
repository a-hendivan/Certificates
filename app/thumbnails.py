"""Renders the first page of each certificate PDF to a PNG thumbnail,
cached on disk so we only render once per file (keyed on mtime)."""

from pathlib import Path
import fitz  # PyMuPDF

THUMB_DIR = Path(__file__).resolve().parent.parent / "thumbnails"
THUMB_DIR.mkdir(exist_ok=True)


def thumbnail_path_for(pdf_path: Path) -> Path:
    return THUMB_DIR / f"{pdf_path.stem}.png"


def ensure_thumbnail(pdf_path: Path, zoom: float = 2.0) -> Path:
    """Return path to a PNG thumbnail of the PDF's first page, generating
    it if missing or if the source PDF is newer than the cached thumbnail."""
    out_path = thumbnail_path_for(pdf_path)

    if out_path.exists() and out_path.stat().st_mtime >= pdf_path.stat().st_mtime:
        return out_path

    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(0)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        pix.save(out_path)
    finally:
        doc.close()

    return out_path
