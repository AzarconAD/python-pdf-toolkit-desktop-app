import os
import shutil
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_toolkit.core.office_bridge import get_soffice_path, run_soffice_conversion
from pdf_toolkit.core.utils import LibreOfficeNotFoundError, ConversionError

soffice_available = shutil.which("soffice") is not None or any(
    Path(p).exists() for p in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
)

@patch("pdf_toolkit.core.office_bridge.Path.exists")
@patch.dict(os.environ, {"LIBREOFFICE_PORTABLE_PATH": "C:\\portable\\soffice.exe"}, clear=True)
def test_get_soffice_path_env_var(mock_exists):
    mock_exists.return_value = True
    p = get_soffice_path()
    assert str(p) == "C:\\portable\\soffice.exe"

@patch("pdf_toolkit.core.office_bridge.Path.exists")
@patch.dict(os.environ, {}, clear=True)
def test_get_soffice_path_not_found(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(LibreOfficeNotFoundError, match="Could not find LibreOffice soffice.exe"):
        get_soffice_path()

@patch("pdf_toolkit.core.office_bridge.get_soffice_path")
@patch("pdf_toolkit.core.office_bridge.subprocess.run")
def test_run_soffice_conversion_success(mock_run, mock_get_soffice, tmp_out_dir, sample_docx):
    # Happy path mocked
    mock_get_soffice.return_value = Path("soffice.exe")
    
    input_path = Path(sample_docx)
    expected_output = tmp_out_dir / f"{input_path.stem}.pdf"
    
    def mock_run_effect(*args, **kwargs):
        expected_output.touch()
        return MagicMock(returncode=0)
    mock_run.side_effect = mock_run_effect
    
    res = run_soffice_conversion(input_path, tmp_out_dir, "pdf")
    assert res == expected_output

@patch("pdf_toolkit.core.office_bridge.get_soffice_path")
@patch("pdf_toolkit.core.office_bridge.subprocess.run")
def test_run_soffice_conversion_timeout(mock_run, mock_get_soffice, tmp_out_dir, sample_docx):
    mock_get_soffice.return_value = Path("soffice.exe")
    
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="soffice", timeout=120)
    
    with pytest.raises(ConversionError, match="timed out"):
        run_soffice_conversion(Path(sample_docx), tmp_out_dir, "pdf", timeout=120)

@patch("pdf_toolkit.core.office_bridge.get_soffice_path")
@patch("pdf_toolkit.core.office_bridge.subprocess.run")
def test_run_soffice_conversion_failure(mock_run, mock_get_soffice, tmp_out_dir, sample_docx):
    mock_get_soffice.return_value = Path("soffice.exe")
    
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="soffice", stderr="Some error")
    
    with pytest.raises(ConversionError, match="Some error"):
        run_soffice_conversion(Path(sample_docx), tmp_out_dir, "pdf")

@patch("pdf_toolkit.core.office_bridge.get_soffice_path")
@patch("pdf_toolkit.core.office_bridge.subprocess.run")
def test_run_soffice_conversion_no_output(mock_run, mock_get_soffice, tmp_out_dir, sample_docx):
    mock_get_soffice.return_value = Path("soffice.exe")
    
    # Subprocess succeeds but doesn't create file
    mock_run.return_value = MagicMock(returncode=0)
    
    with pytest.raises(ConversionError, match="Expected output not found"):
        run_soffice_conversion(Path(sample_docx), tmp_out_dir, "pdf")

@pytest.mark.skipif(not soffice_available, reason="LibreOffice not installed")
def test_run_soffice_conversion_integration(sample_docx, tmp_out_dir):
    res = run_soffice_conversion(Path(sample_docx), tmp_out_dir, "pdf")
    assert res.exists()
    assert os.path.getsize(res) > 0
