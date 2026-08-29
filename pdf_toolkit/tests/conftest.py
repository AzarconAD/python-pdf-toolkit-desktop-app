import os
import pytest
from pathlib import Path

@pytest.fixture
def fixture_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_pdf(fixture_dir):
    return str(fixture_dir / "sample.pdf")

@pytest.fixture
def sample_docx(fixture_dir):
    return str(fixture_dir / "sample.docx")

@pytest.fixture
def sample_png(fixture_dir):
    return str(fixture_dir / "sample.png")

@pytest.fixture
def sample_xlsx(fixture_dir):
    return str(fixture_dir / "sample.xlsx")

@pytest.fixture
def sample_pptx(fixture_dir):
    return str(fixture_dir / "sample.pptx")

@pytest.fixture
def tmp_out_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    return out
