"""Automated tests for the Resume Parsing endpoint (POST /api/resume/parse)."""

import io
import docx
import pymupdf
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def create_sample_pdf(text: str) -> bytes:
    """Generate a clean in-memory PDF containing the specified text."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    content = doc.tobytes()
    doc.close()
    return content


def create_scanned_image_pdf() -> bytes:
    """Generate a PDF containing only a raster image and no selectable text."""
    doc = pymupdf.open()
    page = doc.new_page()
    # Create an RGB pixmap representing an image/scan (using modern PyMuPDF IRect)
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 120), False)
    pix.clear_with(200)
    page.insert_image(pymupdf.Rect(50, 50, 200, 200), pixmap=pix)
    content = doc.tobytes()
    doc.close()
    return content


def create_sample_docx(text: str) -> bytes:
    """Generate a clean in-memory DOCX containing the specified text."""
    doc = docx.Document()
    doc.add_heading("Candidate Resume", level=1)
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_valid_pdf():
    """Verify that a valid PDF resume is successfully parsed."""
    sample_text = (
        "Alice Johnson\n"
        "Senior Software Engineer\n"
        "Proficient in Python, FastAPI, Docker, and PostgreSQL with 6 years experience."
    )
    pdf_bytes = create_sample_pdf(sample_text)

    response = client.post(
        "/api/resume/parse",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Python, FastAPI" in data["text"]
    assert data["metadata"]["file_type"] == "pdf"
    assert data["metadata"]["filename"] == "resume.pdf"
    assert data["metadata"]["page_count"] == 1
    assert data["metadata"]["word_count"] > 10
    assert data["metadata"]["requires_ocr"] is False
    assert data["metadata"]["is_empty_or_whitespace"] is False


def test_parse_valid_docx():
    """Verify that a valid DOCX resume is successfully parsed."""
    sample_text = (
        "Bob Smith\n"
        "Full-Stack Developer\n"
        "Expertise in TypeScript, React, Python, and scalable backend architecture."
    )
    docx_bytes = create_sample_docx(sample_text)

    response = client.post(
        "/api/resume/parse",
        files={
            "file": (
                "bob_resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Bob Smith" in data["text"]
    assert data["metadata"]["file_type"] == "docx"
    assert data["metadata"]["filename"] == "bob_resume.docx"
    assert data["metadata"]["paragraph_count"] is not None
    assert data["metadata"]["word_count"] > 5
    assert data["metadata"]["is_empty_or_whitespace"] is False


def test_reject_unsupported_file_type():
    """Verify that non-PDF/DOCX file formats are rejected with 415."""
    fake_code = b"print('Hello world, I am a python file pretending to be a resume')"

    response = client.post(
        "/api/resume/parse",
        files={"file": ("script.py", fake_code, "text/x-python")},
    )

    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_reject_extension_spoofing():
    """Verify that a file named .pdf containing random text is rejected via magic byte checks."""
    fake_pdf = b"This is just plain text disguised with a .pdf extension"

    response = client.post(
        "/api/resume/parse",
        files={"file": ("malicious.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 415
    assert "File signature does not match" in response.json()["detail"]


def test_reject_empty_file():
    """Verify that an empty (0 bytes) upload is rejected with 400 Bad Request."""
    response = client.post(
        "/api/resume/parse",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_handle_corrupt_pdf():
    """Verify that a corrupt PDF with valid header but invalid trailer is rejected with 422."""
    corrupt_pdf = b"%PDF-1.4\n%corrupted content that cannot be parsed by fitz"

    response = client.post(
        "/api/resume/parse",
        files={"file": ("corrupt.pdf", corrupt_pdf, "application/pdf")},
    )

    assert response.status_code == 422
    assert "corrupt" in response.json()["detail"].lower()


def test_handle_corrupt_docx():
    """Verify that a corrupt DOCX with valid ZIP header but damaged XML is rejected with 422."""
    # Starts with PK ZIP header but contains no valid archive files
    corrupt_docx = b"PK\x03\x04\x14\x00\x00\x00\x08\x00truncated_zip_data"

    response = client.post(
        "/api/resume/parse",
        files={"file": ("corrupt.docx", corrupt_docx, "application/octet-stream")},
    )

    assert response.status_code == 422
    assert "corrupt" in response.json()["detail"].lower()


def test_detect_scanned_pdf_requires_ocr():
    """Verify that an image-only PDF reports requires_ocr=True and explains OCR is needed."""
    scanned_bytes = create_scanned_image_pdf()

    response = client.post(
        "/api/resume/parse",
        files={"file": ("scanned_scan.pdf", scanned_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["metadata"]["requires_ocr"] is True
    assert "OCR" in data["message"]


def test_detect_empty_text_in_document():
    """Verify that a PDF containing whitespace/minimal text is flagged as empty."""
    empty_pdf_bytes = create_sample_pdf("   \n\t   ")

    response = client.post(
        "/api/resume/parse",
        files={"file": ("blank.pdf", empty_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["metadata"]["is_empty_or_whitespace"] is True
    assert "no readable text" in data["message"]


def test_reject_file_exceeding_max_size(monkeypatch):
    """Verify that files exceeding the maximum allowed size are rejected with 413."""
    # Temporarily set max size to 100 bytes for test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)

    large_content = b"%PDF-1.4 " + b"X" * 200

    response = client.post(
        "/api/resume/parse",
        files={"file": ("huge.pdf", large_content, "application/pdf")},
    )

    assert response.status_code == 413
    assert "exceeds the maximum allowed limit" in response.json()["detail"]


def test_update_confirmed_skills_endpoint():
    """Verify that authenticated users can edit, add, or remove confirmed skills."""
    import uuid
    # 1. Register a unique user
    email = f"skills.editor.{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Skills Editor"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload a resume
    pdf_bytes = create_sample_pdf("Skills Editor with Python and Docker experience.")
    upload_res = client.post(
        "/api/resume/parse",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 200

    # 3. Update confirmed skills (add PostgreSQL, remove Docker)
    updated_skills = ["Python", "PostgreSQL", "FastAPI"]
    update_res = client.put(
        "/api/resume/skills",
        json={"skills": updated_skills},
        headers=headers,
    )
    assert update_res.status_code == 200
    res_data = update_res.json()
    canonical_names = [s["canonical_name"] if isinstance(s, dict) else s for s in res_data["skills"]]
    assert canonical_names == updated_skills
    assert "PostgreSQL" in canonical_names

    # 4. Verify record reflects updated skills
    records_res = client.get("/api/resume/records", headers=headers)
    assert records_res.status_code == 200
    rec_id = records_res.json()[0]["id"]
    detail_res = client.get(f"/api/resume/records/{rec_id}", headers=headers)
    assert detail_res.status_code == 200
    rec = detail_res.json()
    rec_skills = [s["canonical_name"] if isinstance(s, dict) else s for s in rec["extracted_skills"]]
    assert rec_skills == updated_skills
