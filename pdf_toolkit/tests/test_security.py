import os
import pytest
from pathlib import Path
from pypdf import PdfWriter, PdfReader
import pikepdf

from core.security import (
    compress_pdf,
    protect_pdf,
    unlock_pdf,
    add_watermark,
    add_page_numbers,
    add_image_watermark
)
from core.utils import InvalidFileError, ConversionError, IncorrectPasswordError

@pytest.fixture
def create_dummy_pdf(tmp_path):
    def _create(name, num_pages=1):
        path = tmp_path / name
        writer = PdfWriter()
        for _ in range(num_pages):
            writer.add_blank_page(width=100, height=100)
        with open(path, "wb") as f:
            writer.write(f)
        return str(path)
    return _create

@pytest.fixture
def create_encrypted_pdf(create_dummy_pdf, tmp_path):
    def _create(name, password="password", num_pages=1):
        # Create unencrypted first
        temp_pdf = create_dummy_pdf(f"temp_{name}", num_pages)
        # Encrypt it
        out_path = str(tmp_path / name)
        pdf = pikepdf.open(temp_pdf)
        enc = pikepdf.Encryption(user=password, owner=password)
        pdf.save(out_path, encryption=enc)
        pdf.close()
        return out_path
    return _create


@pytest.fixture
def create_dummy_image(tmp_path):
    def _create(name="dummy.png"):
        from PIL import Image
        path = tmp_path / name
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(path)
        return str(path)
    return _create

# --- Happy Paths ---

def test_compress_pdf(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "compressed.pdf")
    
    result = compress_pdf(pdf, out_path, quality="low")
    
    assert result.exists()
    assert result.name == "compressed.pdf"
    assert result.stat().st_size > 0

def test_protect_pdf(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "protected.pdf")
    
    result = protect_pdf(pdf, out_path, password="secret")
    
    assert result.exists()
    assert result.stat().st_size > 0
    # verify it's encrypted
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(str(result))

def test_unlock_pdf(create_encrypted_pdf, tmp_path):
    pdf = create_encrypted_pdf("enc.pdf", password="secret", num_pages=2)
    out_path = str(tmp_path / "unlocked.pdf")
    
    result = unlock_pdf(pdf, out_path, password="secret")
    
    assert result.exists()
    assert result.stat().st_size > 0
    # verify it's no longer encrypted
    with pikepdf.open(str(result)) as p:
        assert not p.is_encrypted

def test_add_watermark(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "watermarked.pdf")
    
    result = add_watermark(pdf, out_path, text="CONFIDENTIAL", opacity=0.5, position="diagonal")
    
    assert result.exists()
    assert result.stat().st_size > 0


def test_add_image_watermark(create_dummy_pdf, create_dummy_image, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    img = create_dummy_image("watermark.png")
    out_path = str(tmp_path / "img_watermarked.pdf")
    
    result = add_image_watermark(pdf, out_path, image_path=img, opacity=0.5, position="diagonal", scale=0.5)
    
    assert result.exists()
    assert result.stat().st_size > 0

def test_add_page_numbers(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "numbered.pdf")
    
    result = add_page_numbers(pdf, out_path, position="bottom-right", start_at=1)
    
    assert result.exists()
    assert result.stat().st_size > 0

# --- Function Specific Validations ---

def test_compress_pdf_invalid_quality(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Invalid quality"):
        compress_pdf(pdf, out_path, quality="ultra")

def test_protect_pdf_empty_password(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Password cannot be an empty string"):
        protect_pdf(pdf, out_path, password="")

def test_unlock_pdf_wrong_password(create_encrypted_pdf, tmp_path):
    pdf = create_encrypted_pdf("enc.pdf", password="correct")
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(IncorrectPasswordError):
        unlock_pdf(pdf, out_path, password="wrong")

def test_unlock_pdf_unencrypted_input(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(InvalidFileError, match="not encrypted"):
        unlock_pdf(pdf, out_path, password="any")

def test_add_watermark_empty_text(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="cannot be empty"):
        add_watermark(pdf, out_path, text="")

@pytest.mark.parametrize("func, kwargs", [
    (add_watermark, {"text": "Draft"}),
    (add_image_watermark, {"image_path": "dummy.png"}),
])
def test_watermarks_invalid_position(create_dummy_pdf, create_dummy_image, tmp_path, func, kwargs):
    pdf = create_dummy_pdf("doc.pdf", 1)
    if "image_path" in kwargs:
        kwargs["image_path"] = create_dummy_image(kwargs["image_path"])
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Invalid position"):
        func(pdf, out_path, position="middle", **kwargs)

@pytest.mark.parametrize("func, kwargs", [
    (add_watermark, {"text": "Draft"}),
    (add_image_watermark, {"image_path": "dummy.png"}),
])
def test_watermarks_invalid_opacity(create_dummy_pdf, create_dummy_image, tmp_path, func, kwargs):
    pdf = create_dummy_pdf("doc.pdf", 1)
    if "image_path" in kwargs:
        kwargs["image_path"] = create_dummy_image(kwargs["image_path"])
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Opacity must be between"):
        func(pdf, out_path, opacity=1.5, **kwargs)
    with pytest.raises(ValueError, match="Opacity must be between"):
        func(pdf, out_path, opacity=-0.1, **kwargs)

def test_add_page_numbers_invalid_position(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Invalid position"):
        add_page_numbers(pdf, out_path, position="center-left")


def test_add_image_watermark_invalid_scale(create_dummy_pdf, create_dummy_image, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    img = create_dummy_image("watermark.png")
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Scale must be strictly between"):
        add_image_watermark(pdf, out_path, image_path=img, scale=1.5)
    with pytest.raises(ValueError, match="Scale must be strictly between"):
        add_image_watermark(pdf, out_path, image_path=img, scale=0.0)

def test_add_image_watermark_missing_image(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    missing_img = str(tmp_path / "missing.png")
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(FileNotFoundError):
        add_image_watermark(pdf, out_path, image_path=missing_img)

def test_add_image_watermark_invalid_image_ext(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    txt_img = tmp_path / "wrong.txt"
    txt_img.write_text("hello")
    out_path = str(tmp_path / "out.pdf")
    with pytest.raises(InvalidFileError, match="Invalid image extension"):
        add_image_watermark(pdf, out_path, image_path=str(txt_img))

# --- Shared Validation (Missing file, Wrong ext) ---

@pytest.mark.parametrize("func, kwargs", [
    (compress_pdf, {"output_path": "out.pdf", "quality": "medium"}),
    (protect_pdf, {"output_path": "out.pdf", "password": "pass"}),
    (unlock_pdf, {"output_path": "out.pdf", "password": "pass"}),
    (add_watermark, {"output_path": "out.pdf", "text": "Draft"}),
    (add_page_numbers, {"output_path": "out.pdf", "position": "bottom-center"}),
    (add_image_watermark, {"output_path": "out.pdf", "image_path": "dummy.png"}),
])
def test_missing_file_errors(tmp_path, func, kwargs):
    missing_file = str(tmp_path / "missing.pdf")
    with pytest.raises(FileNotFoundError):
        func(missing_file, **kwargs)

@pytest.mark.parametrize("func, kwargs", [
    (compress_pdf, {"output_path": "out.pdf", "quality": "medium"}),
    (protect_pdf, {"output_path": "out.pdf", "password": "pass"}),
    (unlock_pdf, {"output_path": "out.pdf", "password": "pass"}),
    (add_watermark, {"output_path": "out.pdf", "text": "Draft"}),
    (add_page_numbers, {"output_path": "out.pdf", "position": "bottom-center"}),
    (add_image_watermark, {"output_path": "out.pdf", "image_path": "dummy.png"}),
])
def test_invalid_ext_errors(tmp_path, func, kwargs):
    txt_path = tmp_path / "doc.txt"
    txt_path.write_text("hello")
    with pytest.raises(ValueError, match="Invalid file extension"):
        func(str(txt_path), **kwargs)
