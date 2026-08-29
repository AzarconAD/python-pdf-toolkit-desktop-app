import re
from core.utils import (
    ConversionError, 
    InvalidFileError, 
    LibreOfficeNotFoundError
)

def friendly_message(exc: Exception) -> str:
    """
    Translates a raw backend exception into a clean, user-facing string.
    """
    
    if isinstance(exc, LibreOfficeNotFoundError):
        return "LibreOffice is required for this conversion but could not be found."
        
    if isinstance(exc, InvalidFileError):
        msg = str(exc)
        if "Not a valid PDF file" in msg:
            return "This tool requires a valid PDF file, but the provided file appears to be corrupted or is a different format."
        return "The provided file appears to be invalid or corrupted."
        
    if isinstance(exc, FileNotFoundError):
        return "The selected file could not be found. It may have been moved or deleted."
        
    # 4. Wrong File Extension (ValueError from core.utils.validate_extension)
    if isinstance(exc, ValueError):
        msg = str(exc)
        if "Invalid file extension" in msg and "Allowed extensions are:" in msg:
            # e.g., "Invalid file extension: '.txt'. Allowed extensions are: .pdf"
            match = re.search(r"Allowed extensions are:\s*(.*)", msg)
            if match:
                exts = match.group(1).replace(", ", " or ")
                return f"This tool needs a {exts} file."
        return f"Invalid input: {msg}"
        
    if isinstance(exc, ConversionError):
        msg = str(exc)
        if ":" in msg:
            reason = msg.split(":", 1)[1].strip()
            reason = re.sub(r"^[A-Za-z]+Error\('(.+)'\)$", r"\1", reason)
            return f"Conversion failed: {reason}"
        return "An error occurred during the conversion process."
        
    return f"An unexpected error occurred: {str(exc)}"
