import math
from pathlib import Path
import pymupdf  # PyMuPDF

from .utils import validate_pdf, validate_input_file, InvalidFileError

"""
Element Schema (Shared Contract)

Coordinates convention: x, y, width, height, x1, y1, x2, y2 are all specified in 
PDF point units (1/72 inch). The coordinate origin (0, 0) is at the top-left of the page,
matching PyMuPDF's native page.rect coordinate space. The GUI must convert its canvas
pixel coordinates into this space.

Common fields for all elements:
- "type" (str): The type of element to draw ("text", "shape").
- "page" (int): 0-indexed page number where the element should be applied.

Element-specific fields:
1. type="text":
   - "x", "y" (float): Top-left coordinates.
   - "width", "height" (float): Bounding box dimensions.
   - "content" (str): The text content to insert.
   - "font_size" (float): Font size in points.
   - "color" (str): Text color as a hex string (e.g., "#RRGGBB").
   - "bold" (bool, optional): Whether text is bold (default: False).
   - "italic" (bool, optional): Whether text is italic (default: False).
   - "align" (str, optional): Text alignment, one of "left", "center", "right", "justify" (default: "left").
   - "font_family" (str, optional): Font family, one of "helv", "times", "cour" (default: "helv").

2. type="shape":
   - "shape" (str): One of "rectangle", "circle", "line", "arrow".
   - "x1", "y1" (float): Starting coordinate (or top-left for bounding box).
   - "x2", "y2" (float): Ending coordinate (or bottom-right for bounding box).
   - "color" (str): Stroke color as a hex string (e.g., "#RRGGBB").
   - "stroke_width" (float): Thickness of the line/border in points.
   - "fill" (str | None): Fill color as a hex string (e.g., "#RRGGBB"), or None for no fill.

3. type="image" or type="signature":
   - "x", "y" (float): Top-left coordinates.
   - "width", "height" (float): Dimensions of the image.
   - "image_path" (str): Path to the image file.

4. type="draw":
   - "points" (list[list[float, float]]): List of [x, y] coordinates forming a continuous stroke.
   - "color" (str): Stroke color as a hex string (e.g., "#RRGGBB").
   - "stroke_width" (float): Thickness of the stroke in points.
"""

def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex string like '#RRGGBB' to tuple of (r, g, b) floats in [0, 1]."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color format: {hex_color}")
    
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)

def apply_edits(input_path: str, output_path: str, elements: list[dict]) -> Path:
    """
    Apply a list of text and shape edits to a PDF document.
    
    Args:
        input_path (str): Path to the source PDF.
        output_path (str): Path to save the edited PDF.
        elements (list[dict]): List of edit elements (see module schema).
        
    Returns:
        Path: Path to the saved output PDF.
        
    Raises:
        InvalidFileError: If the input is not a valid PDF.
        ValueError: If an element is malformed or uses unsupported types/values.
    """
    if not input_path.lower().endswith('.pdf'):
        raise InvalidFileError(f"Input file must be a .pdf: {input_path}")
        
    validate_pdf(input_path)
    
    doc = pymupdf.open(input_path)
    
    try:
        for i, element in enumerate(elements):
            element_type = element.get("type")
            page_num = element.get("page")
            
            if element_type is None:
                raise ValueError(f"Element {i} missing required field 'type'.")
            if page_num is None or not isinstance(page_num, int):
                raise ValueError(f"Element {i} missing or invalid required field 'page'.")
            
            if page_num < 0 or page_num >= len(doc):
                raise ValueError(f"Element {i} page number {page_num} out of range (0-{len(doc)-1}).")
                
            page = doc[page_num]
            
            if element_type == "text":
                _apply_text(page, element, i)
            elif element_type == "shape":
                _apply_shape(page, element, i)
            elif element_type in ("image", "signature"):
                _apply_image(page, element, i)
            elif element_type == "draw":
                _apply_draw(page, element, i)
            else:
                raise ValueError(f"Unsupported element type: '{element_type}' in element {i}.")
                
        doc.save(output_path)
        return Path(output_path)
    finally:
        doc.close()

def _apply_text(page: pymupdf.Page, element: dict, index: int) -> None:
    required_keys = ["x", "y", "width", "height", "content", "font_size", "color"]
    for k in required_keys:
        if k not in element:
            raise ValueError(f"Text element {index} missing required field: '{k}'.")
            
    x, y = element["x"], element["y"]
    w, h = element["width"], element["height"]
    content = element["content"]
    font_size = element["font_size"]
    color_hex = element["color"]
    
    # New optional fields
    bold = element.get("bold", False)
    italic = element.get("italic", False)
    align_str = element.get("align", "left")
    font_family = element.get("font_family", "helv")
    
    # Map align
    align_map = {
        "left": pymupdf.TEXT_ALIGN_LEFT,
        "center": pymupdf.TEXT_ALIGN_CENTER,
        "right": pymupdf.TEXT_ALIGN_RIGHT,
        "justify": pymupdf.TEXT_ALIGN_JUSTIFY
    }
    if align_str not in align_map:
        raise ValueError(f"Text element {index} has invalid align value: '{align_str}'. Must be 'left', 'center', 'right', or 'justify'.")
    align_val = align_map[align_str]
    
    # Map font
    font_map = {
        "helv": { (False, False): "helv", (True, False): "hebo", (False, True): "heit", (True, True): "hebi" },
        "times": { (False, False): "tiro", (True, False): "tibo", (False, True): "tiit", (True, True): "tibi" },
        "cour": { (False, False): "cour", (True, False): "cobo", (False, True): "coit", (True, True): "cobi" }
    }
    
    if font_family not in font_map:
        raise ValueError(f"Text element {index} has unsupported font_family: '{font_family}'. Must be 'helv', 'times', or 'cour'.")
        
    font_name = font_map[font_family][(bold, italic)]
    
    rect = pymupdf.Rect(x, y, x + w, y + h)
    color_rgb = _hex_to_rgb(color_hex)
    
    page.insert_textbox(rect, content, fontsize=font_size, fontname=font_name, align=align_val, color=color_rgb)

def _apply_shape(page: pymupdf.Page, element: dict, index: int) -> None:
    required_keys = ["shape", "x1", "y1", "x2", "y2", "color", "stroke_width"]
    for k in required_keys:
        if k not in element:
            raise ValueError(f"Shape element {index} missing required field: '{k}'.")
            
    shape_type = element["shape"]
    x1, y1 = element["x1"], element["y1"]
    x2, y2 = element["x2"], element["y2"]
    color_hex = element["color"]
    stroke_width = element["stroke_width"]
    fill_hex = element.get("fill")
    
    color_rgb = _hex_to_rgb(color_hex)
    fill_rgb = _hex_to_rgb(fill_hex) if fill_hex is not None else None
    
    shape_obj = page.new_shape()
    rect = pymupdf.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    p1 = pymupdf.Point(x1, y1)
    p2 = pymupdf.Point(x2, y2)
    
    if shape_type == "rectangle":
        shape_obj.draw_rect(rect)
    elif shape_type == "circle":
        # Treating (x1,y1) to (x2,y2) as the bounding box for the circle/oval
        shape_obj.draw_oval(rect)
    elif shape_type == "line":
        shape_obj.draw_line(p1, p2)
    elif shape_type == "arrow":
        # Draw the line body
        shape_obj.draw_line(p1, p2)
        
        # Calculate arrowhead manually (triangle at p2)
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L > 0:
            # Unit vector along the line
            ux = dx / L
            uy = dy / L
            # Perpendicular vector
            vx = -uy
            vy = ux
            
            # Head length and width
            H = max(10, stroke_width * 3)
            W = H * 0.5
            
            # Base of the arrowhead triangle
            cx = x2 - H * ux
            cy = y2 - H * uy
            
            # Left and right points of the triangle
            p3 = pymupdf.Point(cx + W * vx, cy + W * vy)
            p4 = pymupdf.Point(cx - W * vx, cy - W * vy)
            
            shape_obj.draw_line(p2, p3)
            shape_obj.draw_line(p2, p4)
            shape_obj.draw_line(p3, p4)
    else:
        raise ValueError(f"Unknown shape type '{shape_type}' in element {index}.")
        
    shape_obj.finish(
        color=color_rgb, 
        fill=fill_rgb if shape_type != "line" else None, 
        width=stroke_width
    )
    shape_obj.commit()

def _apply_image(page: pymupdf.Page, element: dict, index: int) -> None:
    required_keys = ["x", "y", "width", "height", "image_path"]
    for k in required_keys:
        if k not in element:
            raise ValueError(f"Image/Signature element {index} missing required field: '{k}'.")
            
    x, y = element["x"], element["y"]
    w, h = element["width"], element["height"]
    image_path = element["image_path"]
    
    try:
        validate_input_file(image_path, ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'])
    except Exception as e:
        raise InvalidFileError(f"Invalid image file for element {index}: {e}")
        
    rect = pymupdf.Rect(x, y, x + w, y + h)
    page.insert_image(rect, filename=image_path)

def _apply_draw(page: pymupdf.Page, element: dict, index: int) -> None:
    required_keys = ["points", "color", "stroke_width"]
    for k in required_keys:
        if k not in element:
            raise ValueError(f"Draw element {index} missing required field: '{k}'.")
            
    points_data = element["points"]
    if not isinstance(points_data, list):
        raise ValueError(f"Draw element {index} 'points' must be a list.")
        
    if len(points_data) < 2:
        return  # Skip silently if fewer than 2 points
        
    color_hex = element["color"]
    stroke_width = element["stroke_width"]
    color_rgb = _hex_to_rgb(color_hex)
    
    fitz_points = []
    for p in points_data:
        if len(p) != 2:
            raise ValueError(f"Draw element {index} has invalid point format: {p}")
        fitz_points.append(pymupdf.Point(p[0], p[1]))
        
    shape_obj = page.new_shape()
    shape_obj.draw_polyline(fitz_points)
    shape_obj.finish(color=color_rgb, width=stroke_width)
    shape_obj.commit()

def crop_page(input_path: str, output_path: str, page: int, x0: float, y0: float, x1: float, y1: float) -> Path:
    if not input_path.lower().endswith('.pdf'):
        raise InvalidFileError(f"Input file must be a .pdf: {input_path}")
    validate_pdf(input_path)
    
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Invalid crop rect: x1({x1})<=x0({x0}) or y1({y1})<=y0({y0})")
        
    doc = pymupdf.open(input_path)
    try:
        if page < 0 or page >= len(doc):
            raise ValueError(f"Page {page} out of range (0-{len(doc)-1}).")
            
        target_page = doc[page]
        target_page.set_cropbox(pymupdf.Rect(x0, y0, x1, y1))
        
        doc.save(output_path)
        return Path(output_path)
    finally:
        doc.close()

def highlight_text(input_path: str, output_path: str, page: int, quads: list[list[float]]) -> Path:
    if not input_path.lower().endswith('.pdf'):
        raise InvalidFileError(f"Input file must be a .pdf: {input_path}")
    validate_pdf(input_path)
    
    if not quads:
        raise ValueError("Empty quads list provided.")
        
    doc = pymupdf.open(input_path)
    try:
        if page < 0 or page >= len(doc):
            raise ValueError(f"Page {page} out of range (0-{len(doc)-1}).")
            
        target_page = doc[page]
        
        for q in quads:
            if len(q) == 4:
                target_page.add_highlight_annot(pymupdf.Rect(*q))
            elif len(q) == 8:
                ul = pymupdf.Point(q[0], q[1])
                ur = pymupdf.Point(q[2], q[3])
                lr = pymupdf.Point(q[4], q[5])
                ll = pymupdf.Point(q[6], q[7])
                target_page.add_highlight_annot(pymupdf.Quad(ul, ur, ll, lr))
            else:
                raise ValueError("Each quad must have exactly 4 or 8 floats.")
                
        doc.save(output_path)
        return Path(output_path)
    finally:
        doc.close()

def redact_text(input_path: str, output_path: str, page: int, rects: list[list[float]]) -> Path:
    if not input_path.lower().endswith('.pdf'):
        raise InvalidFileError(f"Input file must be a .pdf: {input_path}")
    validate_pdf(input_path)
    
    if not rects:
        raise ValueError("Empty rects list provided.")
        
    doc = pymupdf.open(input_path)
    try:
        if page < 0 or page >= len(doc):
            raise ValueError(f"Page {page} out of range (0-{len(doc)-1}).")
            
        target_page = doc[page]
        
        for r in rects:
            if len(r) != 4:
                raise ValueError(f"Each rect must have exactly 4 floats. Got: {r}")
            target_page.add_redact_annot(pymupdf.Rect(*r))
            
        target_page.apply_redactions()
        
        doc.save(output_path)
        return Path(output_path)
    finally:
        doc.close()
