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
def test_apply_edits_text_line_spacing(create_dummy_pdf, tmp_path):
    import pymupdf
    # We create two elements with different line_spacing and check the delta Y of the second line.
    pdf1 = create_dummy_pdf("doc1.pdf", 1)
    pdf2 = create_dummy_pdf("doc2.pdf", 1)
    out1 = str(tmp_path / "out1.pdf")
    out2 = str(tmp_path / "out2.pdf")
    
    base_element = {
        "type": "text", "page": 0, "x": 100, "y": 100, "width": 200, "height": 100,
        "content": "Line1\nLine2", "font_size": 20, "color": "#000000"
    }
    
    el1 = dict(base_element, line_spacing=1.0)
    el2 = dict(base_element, line_spacing=2.0)
    
    apply_edits(pdf1, out1, [el1])
    apply_edits(pdf2, out2, [el2])
    
    def get_lines(pdf_path):
        doc = pymupdf.open(pdf_path)
        page = doc[0]
        lines = []
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    lines.append(line)
        return lines
        
    lines1 = get_lines(out1)
    lines2 = get_lines(out2)
    
    assert len(lines1) >= 2
    assert len(lines2) >= 2
    
    delta_y1 = lines1[1]["bbox"][1] - lines1[0]["bbox"][1]
    delta_y2 = lines2[1]["bbox"][1] - lines2[0]["bbox"][1]
    
    assert delta_y2 > delta_y1, "Line spacing 2.0 should result in larger Y-delta than 1.0"

def test_apply_edits_text_underline(create_dummy_pdf, tmp_path):
    import pymupdf
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    
    h = 100
    y = 100
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": y, "width": 200, "height": h,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "underline": True
    }]
    
    apply_edits(pdf, out, elements)
    doc = pymupdf.open(out)
    drawings = doc[0].get_drawings()
    assert len(drawings) == 1
    
    # A line consists of two points. Check if they are near y + h * 0.95 (100 + 95 = 195)
    items = drawings[0]["items"]
    assert items[0][0] == "l"  # line
    p1 = items[0][1]
    assert abs(p1.y - 195.0) < 1.0

def test_apply_edits_text_strikethrough(create_dummy_pdf, tmp_path):
    import pymupdf
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    
    h = 100
    y = 100
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": y, "width": 200, "height": h,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "strikethrough": True
    }]
    
    apply_edits(pdf, out, elements)
    doc = pymupdf.open(out)
    drawings = doc[0].get_drawings()
    assert len(drawings) == 1
    
    # A line consists of two points. Check if they are near y + h * 0.55 (100 + 55 = 155)
    items = drawings[0]["items"]
    assert items[0][0] == "l"  # line
    p1 = items[0][1]
    assert abs(p1.y - 155.0) < 1.0

def test_apply_edits_text_highlight(create_dummy_pdf, tmp_path):
    import pymupdf
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": 100, "width": 200, "height": 100,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "highlight_color": "#FF0000"
    }]
    
    apply_edits(pdf, out, elements)
    doc = pymupdf.open(out)
    drawings = doc[0].get_drawings()
    assert len(drawings) == 1
    
    d = drawings[0]
    rect = d["rect"]
    # Check if the drawn rect matches the text bbox (100, 100, 300, 200)
    assert abs(rect.x0 - 100.0) < 1.0
    assert abs(rect.y0 - 100.0) < 1.0
    assert abs(rect.x1 - 300.0) < 1.0
    assert abs(rect.y1 - 200.0) < 1.0
    assert d["fill"] == (1.0, 0.0, 0.0)

def test_apply_edits_text_rotation(create_dummy_pdf, tmp_path):
    import pymupdf
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": 100, "width": 200, "height": 100,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "rotation": 45.0
    }]
    
    apply_edits(pdf, out, elements)
    doc = pymupdf.open(out)
    
    text_dict = doc[0].get_text("dict")
    found_text = False
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                # 45 deg means dir is (0.707, -0.707) approx
                dir_vec = line.get("dir")
                assert abs(dir_vec[0] - 0.707) < 0.01
                found_text = True
    assert found_text

def test_apply_edits_text_opacity_out_of_range(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf("doc.pdf", 1)
    out = str(tmp_path / "out.pdf")
    
    # opacity < 0.0
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": 100, "width": 200, "height": 100,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "opacity": -0.1
    }]
    with pytest.raises(ValueError, match="invalid opacity"):
        apply_edits(pdf, out, elements)
        
    # opacity > 1.0
    elements = [{
        "type": "text", "page": 0, "x": 100, "y": 100, "width": 200, "height": 100,
        "content": "Hello", "font_size": 20, "color": "#000000",
        "opacity": 1.1
    }]
    with pytest.raises(ValueError, match="invalid opacity"):
        apply_edits(pdf, out, elements)



@pytest.mark.parametrize('style', ['dashed', 'dotted'])
def test_apply_edits_shape_stroke_style(create_dummy_pdf, tmp_path, style):
    pdf = create_dummy_pdf('doc.pdf', 1)
    out = str(tmp_path / 'out.pdf')
    elements = [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'stroke_style': style}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()

def test_apply_edits_shape_corner_radius(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf('doc.pdf', 1)
    out = str(tmp_path / 'out.pdf')
    elements = [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'corner_radius': 10.0}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()

def test_apply_edits_shape_fill_opacity(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf('doc.pdf', 1)
    out = str(tmp_path / 'out.pdf')
    elements = [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'fill': '#FF0000', 'fill_opacity': 0.5}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()

def test_apply_edits_shape_rotation(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf('doc.pdf', 1)
    out = str(tmp_path / 'out.pdf')
    elements = [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'rotation': 45.0}]
    res = apply_edits(pdf, out, elements)
    assert Path(res).exists()

def test_apply_edits_shape_invalid(create_dummy_pdf, tmp_path):
    pdf = create_dummy_pdf('doc.pdf', 1)
    out = str(tmp_path / 'out.pdf')
    
    with pytest.raises(ValueError, match='invalid stroke_style'):
        apply_edits(pdf, out, [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'stroke_style': 'invalid'}])
        
    with pytest.raises(ValueError, match='negative corner_radius'):
        apply_edits(pdf, out, [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'corner_radius': -5.0}])
        
    with pytest.raises(ValueError, match='cannot be larger than half'):
        apply_edits(pdf, out, [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'corner_radius': 25.0}])
        
    with pytest.raises(ValueError, match='out of range'):
        apply_edits(pdf, out, [{'type': 'shape', 'page': 0, 'shape': 'rectangle', 'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'color': '#00FF00', 'stroke_width': 2, 'fill_opacity': 1.5}])
