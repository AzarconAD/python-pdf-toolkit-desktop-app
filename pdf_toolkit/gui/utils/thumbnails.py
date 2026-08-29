import pymupdf as fitz
from PySide6.QtGui import QImage, QPixmap

def get_page_count(pdf_path: str) -> int:
    """
    Returns the total number of pages in the given PDF.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        int: Total page count.
    """
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def render_page_thumbnail(pdf_path: str, page_number: int, max_size: int = 150) -> QPixmap:
    """
    Renders a single PDF page to a QPixmap, scaled so its longest side is max_size.
    
    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): 1-indexed page number to render.
        max_size (int): Maximum size of the longest side in pixels. Defaults to 150.
        
    Returns:
        QPixmap: The rendered thumbnail.
    """
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        
        rect = page.rect
        longest_side = max(rect.width, rect.height)
        zoom = max_size / longest_side if longest_side > 0 else 1.0
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Determine QImage format
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            
        # Create QImage from raw bytes
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        
        # Deep copy the QImage to prevent segfaults when 'pix' is garbage collected
        img_copy = img.copy()
        
    return QPixmap.fromImage(img_copy)
