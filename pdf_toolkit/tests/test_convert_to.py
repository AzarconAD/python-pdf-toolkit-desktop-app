import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_toolkit.core.convert_to import docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf
from pdf_toolkit.core.utils import ConversionError

soffice_available = shutil.which("soffice") is not None or any(
    Path(p).exists() for p in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
)

# docx_to_pdf tests
@patch("pdf_toolkit.core.convert_to.run_soffice_conversion")
def test_docx_to_pdf_success(mock_run, sample_docx, tmp_out_dir):
    # Happy path mocked
    expected = tmp_out_dir / "sample.pdf"
    mock_run.return_value = expected
    
    res = docx_to_pdf(sample_docx, str(tmp_out_dir))
    assert res == expected
    assert isinstance(res, Path)
    mock_run.assert_called_once_with(Path(sample_docx), tmp_out_dir, 'pdf')

def test_docx_to_pdf_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        docx_to_pdf("not_exist.docx", str(tmp_out_dir))

def test_docx_to_pdf_wrong_ext(sample_png, tmp_out_dir):
    with pytest.raises(ValueError):
        docx_to_pdf(sample_png, str(tmp_out_dir))

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_docx_to_pdf_integration(sample_docx, tmp_out_dir):
    res = docx_to_pdf(sample_docx, str(tmp_out_dir))
    assert res.exists()
    assert os.path.getsize(res) > 0

# xlsx_to_pdf tests
@patch("pdf_toolkit.core.convert_to.run_soffice_conversion")
def test_xlsx_to_pdf_success(mock_run, sample_xlsx, tmp_out_dir):
    expected = tmp_out_dir / "sample.pdf"
    mock_run.return_value = expected
    
    res = xlsx_to_pdf(sample_xlsx, str(tmp_out_dir))
    assert res == expected
    assert isinstance(res, Path)

def test_xlsx_to_pdf_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        xlsx_to_pdf("not_exist.xlsx", str(tmp_out_dir))

def test_xlsx_to_pdf_wrong_ext(sample_png, tmp_out_dir):
    with pytest.raises(ValueError):
        xlsx_to_pdf(sample_png, str(tmp_out_dir))

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_xlsx_to_pdf_integration(sample_xlsx, tmp_out_dir):
    res = xlsx_to_pdf(sample_xlsx, str(tmp_out_dir))
    assert res.exists()
    assert os.path.getsize(res) > 0

# pptx_to_pdf tests
@patch("pdf_toolkit.core.convert_to.run_soffice_conversion")
def test_pptx_to_pdf_success(mock_run, sample_pptx, tmp_out_dir):
    expected = tmp_out_dir / "sample.pdf"
    mock_run.return_value = expected
    
    res = pptx_to_pdf(sample_pptx, str(tmp_out_dir))
    assert res == expected
    assert isinstance(res, Path)

def test_pptx_to_pdf_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        pptx_to_pdf("not_exist.pptx", str(tmp_out_dir))

def test_pptx_to_pdf_wrong_ext(sample_png, tmp_out_dir):
    with pytest.raises(ValueError):
        pptx_to_pdf(sample_png, str(tmp_out_dir))

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_pptx_to_pdf_integration(sample_pptx, tmp_out_dir):
    res = pptx_to_pdf(sample_pptx, str(tmp_out_dir))
    assert res.exists()
    assert os.path.getsize(res) > 0

# images_to_pdf tests
@patch("pdf_toolkit.core.convert_to.fitz")
def test_images_to_pdf_success(mock_fitz, sample_png, tmp_out_dir):
    out_pdf = str(tmp_out_dir / "out.pdf")
    
    mock_doc = MagicMock()
    mock_fitz.open.return_value = mock_doc
    
    # Mocking doc.save
    def mock_save(path):
        pass
    mock_doc.save.side_effect = mock_save
    
    res = images_to_pdf([sample_png], out_pdf)
    assert res == Path(out_pdf)
    assert isinstance(res, Path)
    mock_doc.save.assert_called_once_with(out_pdf)

def test_images_to_pdf_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        images_to_pdf(["not_exist.png"], str(tmp_out_dir / "out.pdf"))

def test_images_to_pdf_wrong_ext(sample_pdf, tmp_out_dir):
    with pytest.raises(ValueError):
        images_to_pdf([sample_pdf], str(tmp_out_dir / "out.pdf"))
