from pathlib import Path
from pypdf import PdfWriter, PdfReader

from .utils import (
    validate_file_exists,
    validate_extension,
    get_unique_output_path,
    PDFToolkitError,
    InvalidFileError,
    ConversionError
)

def merge_pdfs(input_paths: list[str], output_path: str) -> Path:
    """
    Combines PDFs in the given list order into one file.
    
    Args:
        input_paths (list[str]): List of file paths to PDF files to merge.
        output_path (str): The desired output path for the merged PDF.
        
    Returns:
        Path: The actual path where the merged PDF was saved.
        
    Raises:
        FileNotFoundError: If an input file does not exist.
        ValueError: If an input file is not a PDF, or if the input list is empty.
        InvalidFileError: If an input file cannot be read as a valid PDF.
        ConversionError: If the merge process fails.
    """
    if not input_paths:
        raise ValueError("The input_paths list cannot be empty.")
        
    for p in input_paths:
        validate_file_exists(p)
        validate_extension(p, ['.pdf'])
        
    final_out_path = get_unique_output_path(output_path)
    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        writer = PdfWriter()
        for p in input_paths:
            writer.append(p)
            
        with open(final_out_path, "wb") as f_out:
            writer.write(f_out)
    except Exception as e:
        raise ConversionError(f"Failed to merge PDFs: {e}")
        
    return final_out_path


def split_pdf(input_path: str, output_dir: str, pages_per_file: int = 1, ranges: list[list[int]] | None = None) -> list[Path]:
    """
    Splits a PDF into multiple smaller PDFs based on ranges or a fixed page count per file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_dir (str): Directory where the output files should be saved.
        pages_per_file (int, optional): Number of pages per split file. Defaults to 1.
                                        Ignored if ranges is provided.
        ranges (list[list[int]], optional): A list of [start, end] ranges (1-indexed, inclusive).
                                            If provided, creates one file per range. Defaults to None.
                                            
    Returns:
        list[Path]: List of paths to the generated PDF files in order.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a PDF, or if ranges/pages_per_file are invalid.
        InvalidFileError: If the input file is an invalid PDF or ranges exceed document length.
        ConversionError: If writing the output files fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['.pdf'])
    
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    input_stem = Path(input_path).stem
    generated_files = []
    
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        
        if ranges is not None:
            # Split by specific ranges
            for i, r in enumerate(ranges):
                if len(r) != 2:
                    raise ValueError(f"Range must have exactly 2 elements [start, end], got: {r}")
                start_page, end_page = r
                
                if start_page < 1 or end_page < start_page:
                    raise ValueError(f"Invalid range [start, end]: {r}")
                    
                if end_page > total_pages:
                    raise InvalidFileError(f"Range end ({end_page}) exceeds total pages ({total_pages}).")
                    
                writer = PdfWriter()
                # Convert from 1-indexed inclusive to 0-indexed exclusive for Python slicing logic
                for page_num in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[page_num])
                    
                out_path = out_dir_path / f"{input_stem}_part{i+1}.pdf"
                out_path = get_unique_output_path(str(out_path))
                
                with open(out_path, "wb") as f_out:
                    writer.write(f_out)
                generated_files.append(out_path)
                
        else:
            # Split by pages_per_file sequentially
            if pages_per_file < 1:
                raise ValueError("pages_per_file must be at least 1.")
                
            part_num = 1
            for start_idx in range(0, total_pages, pages_per_file):
                writer = PdfWriter()
                end_idx = min(start_idx + pages_per_file, total_pages)
                
                for page_num in range(start_idx, end_idx):
                    writer.add_page(reader.pages[page_num])
                    
                out_path = out_dir_path / f"{input_stem}_part{part_num}.pdf"
                out_path = get_unique_output_path(str(out_path))
                
                with open(out_path, "wb") as f_out:
                    writer.write(f_out)
                generated_files.append(out_path)
                part_num += 1
                
    except (ValueError, InvalidFileError):
        raise
    except Exception as e:
        raise ConversionError(f"Failed to split PDF: {e}")
        
    return generated_files


def extract_pages(input_path: str, output_path: str, pages: list[int]) -> Path:
    """
    Extracts specific pages from a PDF and saves them to a new file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): The desired output path for the new PDF.
        pages (list[int]): List of 1-indexed page numbers to extract, in the given order.
        
    Returns:
        Path: The actual path where the extracted PDF was saved.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a PDF, or if any page number is out of range.
        InvalidFileError: If the input file is an invalid PDF.
        ConversionError: If the extraction process fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['.pdf'])
    
    final_out_path = get_unique_output_path(output_path)
    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        
        if not pages:
            raise ValueError("No pages specified to extract.")
            
        for p in pages:
            if p < 1 or p > total_pages:
                raise ValueError(f"Page number {p} is out of range (1-{total_pages}).")
                
        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p - 1])
            
        with open(final_out_path, "wb") as f_out:
            writer.write(f_out)
    except (ValueError, InvalidFileError):
        raise
    except Exception as e:
        raise ConversionError(f"Failed to extract pages: {e}")
        
    return final_out_path


def delete_pages(input_path: str, output_path: str, pages: list[int]) -> Path:
    """
    Deletes specific pages from a PDF and saves the rest to a new file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): The desired output path for the new PDF.
        pages (list[int]): List of 1-indexed page numbers to remove.
        
    Returns:
        Path: The actual path where the modified PDF was saved.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a PDF, if any page is out of range, 
                    or if all pages would be deleted.
        InvalidFileError: If the input file is an invalid PDF.
        ConversionError: If the deletion process fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['.pdf'])
    
    final_out_path = get_unique_output_path(output_path)
    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        
        for p in pages:
            if p < 1 or p > total_pages:
                raise ValueError(f"Page number {p} is out of range (1-{total_pages}).")
                
        pages_to_remove = set(pages)
        
        if len(pages_to_remove) >= total_pages:
            raise ValueError("Cannot delete all pages from the PDF.")
            
        writer = PdfWriter()
        for i in range(total_pages):
            if (i + 1) not in pages_to_remove:
                writer.add_page(reader.pages[i])
                
        with open(final_out_path, "wb") as f_out:
            writer.write(f_out)
    except (ValueError, InvalidFileError):
        raise
    except Exception as e:
        raise ConversionError(f"Failed to delete pages: {e}")
        
    return final_out_path


def reorder_pages(input_path: str, output_path: str, new_order: list[int]) -> Path:
    """
    Reorders the pages of a PDF according to the specified sequence.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): The desired output path for the new PDF.
        new_order (list[int]): List of 1-indexed original page numbers in the desired new sequence.
        
    Returns:
        Path: The actual path where the modified PDF was saved.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a PDF, or if new_order does not contain 
                    every original page exactly once.
        InvalidFileError: If the input file is an invalid PDF.
        ConversionError: If the reordering process fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['.pdf'])
    
    final_out_path = get_unique_output_path(output_path)
    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        
        expected_set = set(range(1, total_pages + 1))
        actual_list = new_order
        
        if len(actual_list) != total_pages or set(actual_list) != expected_set:
            raise ValueError(f"new_order must contain every original page exactly once (1 to {total_pages}).")
            
        writer = PdfWriter()
        for p in new_order:
            writer.add_page(reader.pages[p - 1])
            
        with open(final_out_path, "wb") as f_out:
            writer.write(f_out)
    except (ValueError, InvalidFileError):
        raise
    except Exception as e:
        raise ConversionError(f"Failed to reorder pages: {e}")
        
    return final_out_path


def rotate_pages(input_path: str, output_path: str, angle: int, pages: list[int] | None = None) -> Path:
    """
    Rotates specific or all pages of a PDF.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): The desired output path for the new PDF.
        angle (int): The angle to rotate by (90, 180, 270, -90).
        pages (list[int] | None, optional): 1-indexed list of specific pages to rotate. 
                                            If None, rotates all pages.
        
    Returns:
        Path: The actual path where the modified PDF was saved.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a PDF, if angle is invalid, 
                    or if any specified page is out of range.
        InvalidFileError: If the input file is an invalid PDF.
        ConversionError: If the rotation process fails.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, ['.pdf'])
    
    if angle not in (90, 180, 270, -90):
        raise ValueError(f"Angle must be one of 90, 180, 270, -90. Got: {angle}")
        
    # pypdf requires rotation angle as a multiple of 90 clockwise
    # positive degrees are clockwise in pypdf but let's normalize to standard positive representation
    normalized_angle = angle % 360
    
    final_out_path = get_unique_output_path(output_path)
    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        
        pages_to_rotate = set()
        if pages is not None:
            for p in pages:
                if p < 1 or p > total_pages:
                    raise ValueError(f"Page number {p} is out of range (1-{total_pages}).")
                pages_to_rotate.add(p)
        else:
            pages_to_rotate = set(range(1, total_pages + 1))
            
        writer = PdfWriter()
        for i in range(total_pages):
            page = reader.pages[i]
            if (i + 1) in pages_to_rotate:
                # pypdf page.rotate(angle) applies rotation relative to current.
                # Actually, pypdf has page.rotate() or page.rotation depending on version. 
                # Let's check which version of pypdf is installed if it errors, but usually page.rotate() works or page.rotate_clockwise() / page.transfer_rotation_to_content()
                # page.rotate() rotates clockwise by the given degrees in modern pypdf.
                writer.add_page(page).rotate(normalized_angle)
            else:
                writer.add_page(page)
                
        with open(final_out_path, "wb") as f_out:
            writer.write(f_out)
    except (ValueError, InvalidFileError):
        raise
    except Exception as e:
        raise ConversionError(f"Failed to rotate pages: {e}")
        
    return final_out_path
