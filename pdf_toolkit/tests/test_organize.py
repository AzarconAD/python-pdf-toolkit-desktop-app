import os
import pytest
from pathlib import Path
from pypdf import PdfWriter, PdfReader

from core.organize import merge_pdfs, split_pdf, extract_pages, delete_pages, reorder_pages, rotate_pages
from core.utils import InvalidFileError, ConversionError

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

def test_merge_pdfs(create_dummy_pdf, tmp_path):
    pdf1 = create_dummy_pdf("doc1.pdf", 2)
    pdf2 = create_dummy_pdf("doc2.pdf", 3)
    out_path = str(tmp_path / "merged.pdf")
    
    result = merge_pdfs([pdf1, pdf2], out_path)
    
    assert result.exists()
    assert result.name == "merged.pdf"
    
    # Check total pages
    reader = PdfReader(result)
    assert len(reader.pages) == 5

def test_merge_pdfs_empty_list(tmp_path):
    with pytest.raises(ValueError):
        merge_pdfs([], str(tmp_path / "out.pdf"))

def test_merge_pdfs_invalid_ext(tmp_path):
    txt_path = tmp_path / "doc.txt"
    txt_path.write_text("hello")
    with pytest.raises(ValueError):
        merge_pdfs([str(txt_path)], str(tmp_path / "out.pdf"))

def test_merge_pdfs_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        merge_pdfs([str(tmp_path / "missing.pdf")], str(tmp_path / "out.pdf"))

def test_split_pdf_pages_per_file(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 5)
    out_dir = str(tmp_path / "out_dir")
    
    results = split_pdf(pdf, out_dir, pages_per_file=2)
    
    assert len(results) == 3
    assert results[0].name == "doc_part1.pdf"
    assert len(PdfReader(results[0]).pages) == 2
    assert results[1].name == "doc_part2.pdf"
    assert len(PdfReader(results[1]).pages) == 2
    assert results[2].name == "doc_part3.pdf"
    assert len(PdfReader(results[2]).pages) == 1

def test_split_pdf_ranges(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 5)
    out_dir = str(tmp_path / "out_dir_ranges")
    
    results = split_pdf(pdf, out_dir, ranges=[[1, 2], [4, 5]])
    
    assert len(results) == 2
    assert len(PdfReader(results[0]).pages) == 2
    assert len(PdfReader(results[1]).pages) == 2

def test_split_pdf_invalid_range_exceeds(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_dir = str(tmp_path / "out_dir")
    with pytest.raises(InvalidFileError):
        split_pdf(pdf, out_dir, ranges=[[1, 5]])

def test_split_pdf_invalid_range_format(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_dir = str(tmp_path / "out_dir")
    with pytest.raises(ValueError):
        split_pdf(pdf, out_dir, ranges=[[1, 2, 3]])
        
def test_split_pdf_invalid_range_values(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_dir = str(tmp_path / "out_dir")
    with pytest.raises(ValueError):
        split_pdf(pdf, out_dir, ranges=[[2, 1]])

def test_extract_pages(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 5)
    out_path = str(tmp_path / "extracted.pdf")
    
    result = extract_pages(pdf, out_path, pages=[1, 3, 5])
    
    assert result.exists()
    assert len(PdfReader(result).pages) == 3

def test_extract_pages_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "extracted.pdf")
    
    with pytest.raises(ValueError, match="out of range"):
        extract_pages(pdf, out_path, pages=[0, 1])
        
    with pytest.raises(ValueError, match="out of range"):
        extract_pages(pdf, out_path, pages=[1, 4])

def test_delete_pages(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 5)
    out_path = str(tmp_path / "deleted.pdf")
    
    result = delete_pages(pdf, out_path, pages=[2, 4])
    
    assert result.exists()
    assert len(PdfReader(result).pages) == 3

def test_delete_pages_all(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "deleted.pdf")
    
    with pytest.raises(ValueError, match="Cannot delete all pages"):
        delete_pages(pdf, out_path, pages=[1, 2, 3])

def test_delete_pages_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "deleted.pdf")
    
    with pytest.raises(ValueError, match="out of range"):
        delete_pages(pdf, out_path, pages=[4])

def test_reorder_pages(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "reordered.pdf")
    
    result = reorder_pages(pdf, out_path, new_order=[3, 1, 2])
    
    assert result.exists()
    assert len(PdfReader(result).pages) == 3

def test_reorder_pages_missing_page(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "reordered.pdf")
    
    with pytest.raises(ValueError, match="contain every original page exactly once"):
        reorder_pages(pdf, out_path, new_order=[1, 2])

def test_reorder_pages_duplicate_page(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "reordered.pdf")
    
    with pytest.raises(ValueError, match="contain every original page exactly once"):
        reorder_pages(pdf, out_path, new_order=[1, 2, 2])

def test_rotate_pages_all(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "rotated.pdf")
    
    result = rotate_pages(pdf, out_path, angle=90)
    
    assert result.exists()
    reader = PdfReader(result)
    assert len(reader.pages) == 2
    # In pypdf, rotate adds to the rotation, let's just check it doesn't crash
    # or check the rotation attribute if needed.

def test_rotate_pages_specific(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 3)
    out_path = str(tmp_path / "rotated.pdf")
    
    result = rotate_pages(pdf, out_path, angle=-90, pages=[1, 3])
    
    assert result.exists()

def test_rotate_pages_invalid_angle(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "rotated.pdf")
    
    with pytest.raises(ValueError, match="Angle must be one of"):
        rotate_pages(pdf, out_path, angle=45)

def test_rotate_pages_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 2)
    out_path = str(tmp_path / "rotated.pdf")
    
    with pytest.raises(ValueError, match="out of range"):
        rotate_pages(pdf, out_path, angle=180, pages=[3])

@pytest.mark.parametrize("func, kwargs", [
    (split_pdf, {"output_dir": "out"}),
    (extract_pages, {"output_path": "out.pdf", "pages": [1]}),
    (delete_pages, {"output_path": "out.pdf", "pages": [1]}),
    (reorder_pages, {"output_path": "out.pdf", "new_order": [1]}),
    (rotate_pages, {"output_path": "out.pdf", "angle": 90}),
])
def test_missing_file_errors(tmp_path, func, kwargs):
    missing_file = str(tmp_path / "missing.pdf")
    with pytest.raises(FileNotFoundError):
        func(missing_file, **kwargs)

@pytest.mark.parametrize("func, kwargs", [
    (split_pdf, {"output_dir": "out"}),
    (extract_pages, {"output_path": "out.pdf", "pages": [1]}),
    (delete_pages, {"output_path": "out.pdf", "pages": [1]}),
    (reorder_pages, {"output_path": "out.pdf", "new_order": [1]}),
    (rotate_pages, {"output_path": "out.pdf", "angle": 90}),
])
def test_invalid_ext_errors(tmp_path, func, kwargs):
    txt_path = tmp_path / "doc.txt"
    txt_path.write_text("hello")
    with pytest.raises(ValueError, match="Invalid file extension"):
        func(str(txt_path), **kwargs)
