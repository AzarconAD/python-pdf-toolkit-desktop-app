import os
from pathlib import Path
import io
import contextlib

with contextlib.redirect_stdout(io.StringIO()):
    from pdf2docx import Converter

import pymupdf  # PyMuPDF
from .utils import validate_pdf, ensure_output_dir, ConversionError
from .office_bridge import run_soffice_conversion

def pdf_to_docx(input_path: str, output_dir: str) -> Path:
    """
    Convert PDF to .docx using pdf2docx library.
    
    Args:
        input_path (str): Path to input PDF file.
        output_dir (str): Directory to save the resulting .docx.
        
    Returns:
        Path: Output .docx path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
        ConversionError: If the conversion fails.
    """
    validate_pdf(input_path)
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    in_p = Path(input_path)
    out_p = Path(output_dir) / f"{in_p.stem}.docx"
    
    try:
        cv = Converter(input_path)
        cv.convert(str(out_p), start=0, end=None)
        cv.close()
    except Exception as e:
        raise ConversionError(f"Failed to convert PDF to DOCX: {e}")
        
    return out_p

def pdf_to_xlsx(input_path: str, output_dir: str) -> Path:
    """
    Convert PDF to .xlsx via LibreOffice.
    
    Args:
        input_path (str): Path to input PDF file.
        output_dir (str): Directory to save the resulting .xlsx.
        
    Returns:
        Path: Output .xlsx path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
        ConversionError: If the conversion fails.
    """
    validate_pdf(input_path)
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    return run_soffice_conversion(Path(input_path), Path(output_dir), 'xlsx')

def pdf_to_pptx(input_path: str, output_dir: str) -> Path:
    """
    Convert PDF to .pptx via LibreOffice.
    
    Args:
        input_path (str): Path to input PDF file.
        output_dir (str): Directory to save the resulting .pptx.
        
    Returns:
        Path: Output .pptx path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
        ConversionError: If the conversion fails.
    """
    validate_pdf(input_path)
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    return run_soffice_conversion(Path(input_path), Path(output_dir), 'pptx')

def pdf_to_images(input_path: str, output_dir: str, image_format: str = 'png', dpi: int = 200) -> list[Path]:
    """
    Render each PDF page to an image file using PyMuPDF.
    
    Args:
        input_path (str): Path to input PDF file.
        output_dir (str): Directory to save resulting images.
        image_format (str): Image format ('png' or 'jpg'). Defaults to 'png'.
        dpi (int): DPI for rendering. Defaults to 200.
        
    Returns:
        list[Path]: List of output image paths.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
        ConversionError: If the conversion fails or an invalid image format is provided.
    """
    validate_pdf(input_path)
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    if image_format not in ['png', 'jpg', 'jpeg']:
        raise ConversionError(f"Unsupported image format: {image_format}")
        
    output_paths = []
    stem = Path(input_path).stem
    
    try:
        doc = pymupdf.open(input_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            
            output_name = f"{stem}_page{page_num + 1}.{image_format}"
            out_path = Path(output_dir) / output_name
            
            if image_format in ['jpg', 'jpeg']:
                pix.save(str(out_path), output_opt="jpeg")
            else:
                pix.save(str(out_path))
                
            output_paths.append(out_path)
    except Exception as e:
        raise ConversionError(f"Failed to convert PDF to images: {e}")
        
    return output_paths
