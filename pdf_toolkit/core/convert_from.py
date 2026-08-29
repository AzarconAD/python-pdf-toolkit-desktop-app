import os
import pymupdf  # PyMuPDF
from pathlib import Path
from .utils import validate_file_exists, validate_extension, ensure_output_dir, ConversionError
from .office_bridge import run_soffice_conversion

def docx_to_pdf(input_path: str, output_dir: str) -> Path:
    """
    Convert .docx to PDF via LibreOffice.
    
    Args:
        input_path (str): Path to input .docx file.
        output_dir (str): Path to save the resulting PDF.
        
    Returns:
        Path: Output PDF path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file does not have a .docx extension.
        ConversionError: If the conversion fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['docx'])
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    return run_soffice_conversion(Path(input_path), Path(output_dir), 'pdf')

def xlsx_to_pdf(input_path: str, output_dir: str) -> Path:
    """
    Convert .xlsx to PDF via LibreOffice.
    
    Args:
        input_path (str): Path to input .xlsx file.
        output_dir (str): Path to save the resulting PDF.
        
    Returns:
        Path: Output PDF path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file does not have a .xlsx extension.
        ConversionError: If the conversion fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['xlsx'])
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    return run_soffice_conversion(Path(input_path), Path(output_dir), 'pdf')

def pptx_to_pdf(input_path: str, output_dir: str) -> Path:
    """
    Convert .pptx to PDF via LibreOffice.
    
    Args:
        input_path (str): Path to input .pptx file.
        output_dir (str): Path to save the resulting PDF.
        
    Returns:
        Path: Output PDF path.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file does not have a .xlsx extension.
        ConversionError: If the conversion fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['pptx'])
    ensure_output_dir(os.path.join(output_dir, "dummy"))
    
    return run_soffice_conversion(Path(input_path), Path(output_dir), 'pdf')

def images_to_pdf(input_paths: list[str], output_path: str) -> Path:
    """
    Convert a list of image files to a single PDF using PyMuPDF.
    
    Args:
        input_paths (list[str]): List of image file paths (jpg, jpeg, png).
        output_path (str): Full path to save the resulting PDF.
        
    Returns:
        Path: Output PDF path.
        
    Raises:
        FileNotFoundError: If any input file does not exist.
        ValueError: If any input file does not have an allowed extension.
        ConversionError: If no images are provided or PyMuPDF fails.
    """
    if not input_paths:
        raise ConversionError("No input images provided.")
        
    for p in input_paths:
        validate_file_exists(p)
        validate_extension(p, ['jpg', 'jpeg', 'png'])
        
    ensure_output_dir(output_path)
    
    try:
        doc = pymupdf.open()
        for img_path in input_paths:
            img_doc = pymupdf.open(img_path)
            pdf_bytes = img_doc.convert_to_pdf()
            pdf_doc = pymupdf.open("pdf", pdf_bytes)
            doc.insert_pdf(pdf_doc)
            
        doc.save(output_path)
        doc.close()
    except Exception as e:
        raise ConversionError(f"Failed to convert images to PDF: {e}")
        
    return Path(output_path)
