import pytest
from pathlib import Path
from pdf_toolkit.core.utils import (
    validate_file_exists,
    validate_extension,
    get_unique_output_path,
    validate_pdf,
    validate_input_file,
    InvalidFileError
)

def test_validate_file_exists(sample_png):
    # Happy path
    res = validate_file_exists(sample_png)
    assert isinstance(res, Path)
    assert res == Path(sample_png)

def test_validate_file_exists_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="The file was not found"):
        validate_file_exists(str(tmp_path / "missing.txt"))

def test_validate_extension():
    # Happy path
    validate_extension("file.txt", ["txt", ".csv"])
    validate_extension("file.CSV", ["txt", "csv"])

def test_validate_extension_wrong():
    # Wrong extension
    with pytest.raises(ValueError, match="Invalid file extension"):
        validate_extension("file.pdf", ["txt", "csv"])

def test_validate_pdf(sample_pdf):
    # Happy path
    validate_pdf(sample_pdf)

def test_validate_pdf_missing(tmp_path):
    # Missing input file
    with pytest.raises(FileNotFoundError):
        validate_pdf(str(tmp_path / "missing.pdf"))

def test_validate_pdf_wrong_header(sample_png):
    # Exists, but not a PDF
    with pytest.raises(InvalidFileError, match="Not a valid PDF file"):
        validate_pdf(sample_png)

def test_validate_input_file(sample_png):
    # Happy path
    validate_input_file(sample_png, ["png"])

def test_validate_input_file_missing(tmp_path):
    # Missing input file
    with pytest.raises(FileNotFoundError):
        validate_input_file(str(tmp_path / "missing.png"), ["png"])

def test_validate_input_file_wrong_extension(sample_png):
    # Wrong extension
    with pytest.raises(ValueError):
        validate_input_file(sample_png, ["jpg"])

def test_get_unique_output_path(tmp_path):
    base = tmp_path / "out.pdf"
    
    # 1. Doesn't exist initially
    res = get_unique_output_path(str(base))
    assert res == base
    
    # 2. Exists once
    base.write_text("data")
    res2 = get_unique_output_path(str(base))
    assert res2.name == "out (1).pdf"
    
    # 3. Exists twice
    res2.write_text("data2")
    res3 = get_unique_output_path(str(base))
    assert res3.name == "out (2).pdf"
