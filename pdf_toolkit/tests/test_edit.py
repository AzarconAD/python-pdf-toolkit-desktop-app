import pytest
from pathlib import Path
from pypdf import PdfWriter
from core.edit import apply_edits, crop_page, highlight_text, redact_text
from core.utils import InvalidFileError

@pytest.fixture
def create_dummy_pdf(tmp_path):
    def _create(name, num_pages=1):
        path = tmp_path / name
        writer = PdfWriter()
        for _ in range(num_pages):
            writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        return str(path)
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

def test_apply_edits_text_old_style(create_dummy_pdf, tmp_path):
    # Backward compatibility check for elements with no new fields
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "text", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50, "content": "hello", "font_size": 12, "color": "#FF0000"}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

@pytest.mark.parametrize("align", ["left", "center", "right", "justify"])
@pytest.mark.parametrize("font_family", ["helv", "times", "cour"])
@pytest.mark.parametrize("bold", [True, False])
@pytest.mark.parametrize("italic", [True, False])
def test_apply_edits_text_new_style(create_dummy_pdf, tmp_path, align, font_family, bold, italic):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / f"out_{align}_{font_family}_{bold}_{italic}.pdf")
    elements = [{
        "type": "text", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50,
        "content": "hello", "font_size": 12, "color": "#FF0000",
        "align": align, "font_family": font_family, "bold": bold, "italic": italic
    }]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

def test_apply_edits_text_combined_special(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{
        "type": "text", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50,
        "content": "hello", "font_size": 12, "color": "#FF0000",
        "align": "justify", "font_family": "times", "bold": True, "italic": True
    }]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

@pytest.mark.parametrize("shape_type", ["rectangle", "circle", "line", "arrow"])
def test_apply_edits_shape(create_dummy_pdf, tmp_path, shape_type):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "shape", "page": 0, "shape": shape_type, "x1": 10, "y1": 10, "x2": 50, "y2": 50, "color": "#00FF00", "stroke_width": 2, "fill": None}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

def test_apply_edits_image(create_dummy_pdf, create_dummy_image, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    img = create_dummy_image()
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "image", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50, "image_path": img}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

def test_apply_edits_signature(create_dummy_pdf, create_dummy_image, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    img = create_dummy_image()
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "signature", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50, "image_path": img}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

def test_apply_edits_draw(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "draw", "page": 0, "points": [[10, 10], [20, 20], [30, 10]], "color": "#0000FF", "stroke_width": 3}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0

# Negative tests

def test_apply_edits_missing_file(tmp_path):
    pdf = str(tmp_path / "nonexistent.pdf")
    out = str(tmp_path / "out.pdf")
    with pytest.raises(FileNotFoundError):
        apply_edits(pdf, out, [])

def test_apply_edits_wrong_extension(tmp_path):
    pdf = str(tmp_path / "doc.txt")
    Path(pdf).write_text("dummy")
    out = str(tmp_path / "out.pdf")
    with pytest.raises(InvalidFileError):
        apply_edits(pdf, out, [])

def test_apply_edits_unknown_element_type(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "unknown", "page": 0}]
    with pytest.raises(ValueError, match="Unsupported element type"):
        apply_edits(pdf, out, elements)

def test_apply_edits_out_of_range_page(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{"type": "text", "page": 1, "x": 10, "y": 10, "width": 50, "height": 50, "content": "hi", "font_size": 12, "color": "#000"}]
    with pytest.raises(ValueError, match="out of range"):
        apply_edits(pdf, out, elements)

def test_apply_edits_invalid_align(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{
        "type": "text", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50,
        "content": "hi", "font_size": 12, "color": "#000", "align": "bottom"
    }]
    with pytest.raises(ValueError, match="invalid align value: 'bottom'"):
        apply_edits(pdf, out, elements)
        
def test_apply_edits_invalid_font_family(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    elements = [{
        "type": "text", "page": 0, "x": 10, "y": 10, "width": 50, "height": 50,
        "content": "hi", "font_size": 12, "color": "#000", "font_family": "comic_sans"
    }]
    with pytest.raises(ValueError, match="unsupported font_family: 'comic_sans'"):
        apply_edits(pdf, out, elements)

@pytest.mark.parametrize("elements,expected_match", [
    ([{"page": 0, "x": 10}], "missing required field 'type'"),
    ([{"type": "text", "x": 10}], "missing or invalid required field 'page'"),
    ([{"type": "text", "page": 0}], "missing required field"),
    ([{"type": "shape", "page": 0, "shape": "rectangle"}], "missing required field"),
    ([{"type": "image", "page": 0, "x": 10}], "missing required field"),
    ([{"type": "draw", "page": 0}], "missing required field"),
])
def test_apply_edits_missing_required_fields(create_dummy_pdf, tmp_path, elements, expected_match):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match=expected_match):
        apply_edits(pdf, out, elements)

# --- crop_page ---
def test_crop_page_happy(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    res = crop_page(pdf, out, 0, 10, 10, 50, 50)
    assert Path(res).exists()

def test_crop_page_invalid_rect(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Invalid crop rect"):
        crop_page(pdf, out, 0, 50, 50, 10, 10)

def test_crop_page_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        crop_page(str(tmp_path / "no.pdf"), str(tmp_path / "out.pdf"), 0, 10, 10, 50, 50)

def test_crop_page_wrong_extension(tmp_path):
    pdf = str(tmp_path / "doc.txt")
    Path(pdf).write_text("dummy")
    with pytest.raises(InvalidFileError):
        crop_page(pdf, str(tmp_path / "out.pdf"), 0, 10, 10, 50, 50)

def test_crop_page_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    with pytest.raises(ValueError, match="out of range"):
        crop_page(pdf, str(tmp_path / "out.pdf"), 1, 10, 10, 50, 50)

# --- highlight_text ---
def test_highlight_text_happy(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    res = highlight_text(pdf, out, 0, [[10.0, 10.0, 50.0, 50.0], [10.0, 10.0, 50.0, 10.0, 50.0, 50.0, 10.0, 50.0]])
    assert Path(res).exists()

def test_highlight_text_empty(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Empty quads list"):
        highlight_text(pdf, out, 0, [])

def test_highlight_text_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        highlight_text(str(tmp_path / "no.pdf"), str(tmp_path / "out.pdf"), 0, [[10, 10, 50, 50]])

def test_highlight_text_wrong_extension(tmp_path):
    pdf = str(tmp_path / "doc.txt")
    Path(pdf).write_text("dummy")
    with pytest.raises(InvalidFileError):
        highlight_text(pdf, str(tmp_path / "out.pdf"), 0, [[10, 10, 50, 50]])

def test_highlight_text_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    with pytest.raises(ValueError, match="out of range"):
        highlight_text(pdf, str(tmp_path / "out.pdf"), 1, [[10, 10, 50, 50]])

# --- redact_text ---
def test_redact_text_happy(tmp_path):
    import pymupdf
    pdf = str(tmp_path / "doc_with_text.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(pymupdf.Point(50, 50), "Top Secret Data")
    doc.save(pdf)
    doc.close()
    
    out = str(tmp_path / "out.pdf")
    res = redact_text(pdf, out, 0, [[40, 30, 100, 60]])
    
    doc2 = pymupdf.open(res)
    text = doc2[0].get_text()
    doc2.close()
    
    assert "Secret" not in text

def test_redact_text_empty(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    with pytest.raises(ValueError, match="Empty rects list"):
        redact_text(pdf, out, 0, [])

def test_redact_text_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        redact_text(str(tmp_path / "no.pdf"), str(tmp_path / "out.pdf"), 0, [[10, 10, 50, 50]])

def test_redact_text_wrong_extension(tmp_path):
    pdf = str(tmp_path / "doc.txt")
    Path(pdf).write_text("dummy")
    with pytest.raises(InvalidFileError):
        redact_text(pdf, str(tmp_path / "out.pdf"), 0, [[10, 10, 50, 50]])

def test_redact_text_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    with pytest.raises(ValueError, match="out of range"):
        redact_text(pdf, str(tmp_path / "out.pdf"), 1, [[10, 10, 50, 50]])
