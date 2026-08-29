import os
import subprocess
from pathlib import Path
from .utils import ConversionError, LibreOfficeNotFoundError

def get_soffice_path() -> Path:
    """
    Find LibreOffice soffice.exe executable.
    
    Args:
        None
    
    Checks the LIBREOFFICE_PORTABLE_PATH environment variable first,
    then checks common Windows installation locations.
    
    Returns:
        Path: Path to the soffice executable.
        
    Raises:
        LibreOfficeNotFoundError: If soffice cannot be found.
    """
    # TODO Phase 5: point at bundled portable copy
    env_path = os.environ.get("LIBREOFFICE_PORTABLE_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
            
    common_paths = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files\LibreOffice 7\program\soffice.exe"),
        Path(r"C:\Program Files\LibreOffice 24\program\soffice.exe"),
    ]
    
    for p in common_paths:
        if p.exists():
            return p
            
    raise LibreOfficeNotFoundError("Could not find LibreOffice soffice.exe in common locations or LIBREOFFICE_PORTABLE_PATH")

def run_soffice_conversion(input_path: Path, output_dir: Path, target_format: str, timeout: int = 120) -> Path:
    """
    Run LibreOffice headless to convert a file to a target format.
    
    Args:
        input_path (Path): Path to the input file.
        output_dir (Path): Directory where the output should be saved.
        target_format (str): The target format extension (e.g., 'pdf', 'docx').
        timeout (int): Timeout in seconds. Defaults to 120.
        
    Returns:
        Path: Path to the generated output file.
        
    Raises:
        ConversionError: If the process times out, fails, or fails to produce output.
    """
    soffice = get_soffice_path()
    
    args = [
        str(soffice),
        "--headless",
        "--convert-to", target_format,
        "--outdir", str(output_dir),
        str(input_path)
    ]
    
    try:
        result = subprocess.run(
            args,
            check=True,
            timeout=timeout,
            capture_output=True,
            text=True
        )
    except subprocess.TimeoutExpired:
        raise ConversionError(f"LibreOffice timed out after {timeout}s")
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"LibreOffice conversion failed: {e.stderr}")
    except Exception as e:
        raise ConversionError(f"Unexpected error running LibreOffice: {e}")
        
    expected = output_dir / f"{input_path.stem}.{target_format}"
    if not expected.exists():
        raise ConversionError(f"Expected output not found: {expected}")
        
    return expected
