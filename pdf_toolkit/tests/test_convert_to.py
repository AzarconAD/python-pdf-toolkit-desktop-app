import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_toolkit.core.convert_to import pdf_to_docx, pdf_to_xlsx, pdf_to_images, pdf_to_pptx
from pdf_toolkit.core.utils import ConversionError

soffice_available = shutil.which("soffice") is not None or any(
    Path(p).exists() for p in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
)

# pdf_to_docx tests
@patch("pdf_toolkit.core.convert_to.Converter")
def test_pdf_to_docx_success(mock_converter_class, sample_pdf, tmp_out_dir):
    mock_cv = MagicMock()
    mock_converter_class.return_value = mock_cv
    
    res = pdf_to_docx(sample_pdf, str(tmp_out_dir))
    expected_out = tmp_out_dir / "sample.docx"
    
    assert res == expected_out
    assert isinstance(res, Path)
    mock_cv.convert.assert_called_once_with(str(expected_out), start=0, end=None)
    mock_cv.close.assert_called_once()

def test_pdf_to_docx_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        pdf_to_docx("not_exist.pdf", str(tmp_out_dir))

def test_pdf_to_docx_wrong_ext(sample_png, tmp_out_dir):
    # Using sample_png instead of a PDF
    # This actually throws InvalidFileError for wrong %PDF header because validate_pdf relies on header, not extension
    from pdf_toolkit.core.utils import InvalidFileError
    with pytest.raises(InvalidFileError):
        pdf_to_docx(sample_png, str(tmp_out_dir))

# pdf_to_xlsx tests
@patch("pdf_toolkit.core.convert_to.run_soffice_conversion")
def test_pdf_to_xlsx_success(mock_run, sample_pdf, tmp_out_dir):
    expected_out = tmp_out_dir / "sample.xlsx"
    mock_run.return_value = expected_out
    
    res = pdf_to_xlsx(sample_pdf, str(tmp_out_dir))
    assert res == expected_out
    assert isinstance(res, Path)
    mock_run.assert_called_once_with(Path(sample_pdf), tmp_out_dir, 'xlsx')

def test_pdf_to_xlsx_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        pdf_to_xlsx("not_exist.pdf", str(tmp_out_dir))

def test_pdf_to_xlsx_wrong_ext(sample_png, tmp_out_dir):
    from pdf_toolkit.core.utils import InvalidFileError
    with pytest.raises(InvalidFileError):
        pdf_to_xlsx(sample_png, str(tmp_out_dir))

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_pdf_to_xlsx_integration(sample_pdf, tmp_out_dir):
    res = pdf_to_xlsx(sample_pdf, str(tmp_out_dir))
    assert res.exists()
    assert os.path.getsize(res) > 0

# pdf_to_pptx tests
@patch("pdf_toolkit.core.convert_to.run_soffice_conversion")
def test_pdf_to_pptx_success(mock_run, sample_pdf, tmp_out_dir):
    expected_out = tmp_out_dir / "sample.pptx"
    mock_run.return_value = expected_out
    
    res = pdf_to_pptx(sample_pdf, str(tmp_out_dir))
    assert res == expected_out
    assert isinstance(res, Path)
    mock_run.assert_called_once_with(Path(sample_pdf), tmp_out_dir, 'pptx')

def test_pdf_to_pptx_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        pdf_to_pptx("not_exist.pdf", str(tmp_out_dir))

def test_pdf_to_pptx_wrong_ext(sample_png, tmp_out_dir):
    from pdf_toolkit.core.utils import InvalidFileError
    with pytest.raises(InvalidFileError):
        pdf_to_pptx(sample_png, str(tmp_out_dir))

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_pdf_to_pptx_integration(sample_pdf, tmp_out_dir):
    res = pdf_to_pptx(sample_pdf, str(tmp_out_dir))
    assert res.exists()
    assert os.path.getsize(res) > 0

# pdf_to_images tests
@patch("pdf_toolkit.core.convert_to.pymupdf.open")
def test_pdf_to_images_success(mock_fitz_open, sample_pdf, tmp_out_dir):
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    res = pdf_to_images(sample_pdf, str(tmp_out_dir), image_format='png', dpi=200)
    
    assert len(res) == 2
    assert isinstance(res[0], Path)
    assert res[0] == tmp_out_dir / "sample_page1.png"
    assert res[1] == tmp_out_dir / "sample_page2.png"
    assert mock_pix.save.call_count == 2
    mock_page.get_pixmap.assert_called_with(dpi=200)

def test_pdf_to_images_missing(tmp_out_dir):
    with pytest.raises(FileNotFoundError):
        pdf_to_images("not_exist.pdf", str(tmp_out_dir))

def test_pdf_to_images_wrong_ext(sample_png, tmp_out_dir):
    from pdf_toolkit.core.utils import InvalidFileError
    with pytest.raises(InvalidFileError):
        pdf_to_images(sample_png, str(tmp_out_dir))
