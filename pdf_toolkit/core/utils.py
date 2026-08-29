import os
from pathlib import Path

class PDFToolkitError(Exception):
    """Base exception for PDF Toolkit."""
    pass

class ConversionError(PDFToolkitError):
    """Raised when conversion fails."""
    pass

class InvalidFileError(PDFToolkitError):
    """Raised when an input file is invalid."""
    pass

class LibreOfficeNotFoundError(PDFToolkitError):
    """Raised when LibreOffice cannot be found."""
    pass

def validate_file_exists(path: str) -> Path:
    """
    Check if the given path exists on disk.
    
    Args:
        path (str): The file path to check.
        
    Returns:
        Path: A pathlib.Path object of the existing file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"The file was not found: {path}")
    return p

def validate_extension(path: str, allowed: list[str]) -> None:
    """
    Check if the file has one of the allowed extensions.
    
    Args:
        path (str): The file path to check.
        allowed (list[str]): A list of allowed extensions (e.g., ['pdf', '.docx']).
        
    Returns:
        None
        
    Raises:
        ValueError: If the file's extension is not in the allowed list.
    """
    p = Path(path)
    allowed_normalized = [ext.lower() if ext.startswith('.') else f".{ext.lower()}" for ext in allowed]
    
    if p.suffix.lower() not in allowed_normalized:
        raise ValueError(f"Invalid file extension: '{p.suffix}'. Allowed extensions are: {', '.join(allowed_normalized)}")

def validate_pdf(path: str) -> None:
    """
    Validate that the path exists and is a readable PDF.
    
    Args:
        path (str): The path to the PDF file.
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If the file does not exist.
        InvalidFileError: If the file is not readable or does not have a %PDF header.
    """
    validate_file_exists(path)
    
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise InvalidFileError(f"Not a valid PDF file: {path}")
    except InvalidFileError:
        raise
    except Exception as e:
        raise InvalidFileError(f"Failed to read file {path}: {e}")

def validate_input_file(path: str, extensions: list[str]) -> None:
    """
    Validate that the file exists and has one of the allowed extensions.
    
    Args:
        path (str): The path to the file.
        extensions (list[str]): Allowed extensions (with or without dot).
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file's extension is not in the allowed list.
    """
    validate_file_exists(path)
    validate_extension(path, extensions)

def get_unique_output_path(desired_path: str) -> Path:
    """
    Get a unique file path based on the desired path.
    If the desired path already exists, appends ' (1)', ' (2)', etc. to the stem
    until a non-existing path is found.
    
    Args:
        desired_path (str): The initial desired file path.
        
    Returns:
        Path: A unique pathlib.Path object that does not currently exist.
    """
    p = Path(desired_path)
    if not p.exists():
        return p
        
    directory = p.parent
    stem = p.stem
    suffix = p.suffix
    
    counter = 1
    while True:
        new_path = directory / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

def ensure_output_dir(path: str) -> None:
    """
    Create parent directories of the given path if they don't exist.
    
    Args:
        path (str): The target file path.
        
    Returns:
        None
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
