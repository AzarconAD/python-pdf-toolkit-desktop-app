import os
import shutil
import subprocess
from pathlib import Path
from .utils import ConversionError, LibreOfficeNotFoundError

def get_soffice_path() -> Path:
    """
    Find LibreOffice soffice.exe executable.
    
    Args:
        None
    
    Checks the LIBREOFFICE_PORTABLE_PATH environment variable first,
    then checks common Windows installation locations, then falls back
    to shutil.which() in case soffice is on the system PATH.
    
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
        Path(__file__).parent.parent / "LibreOfficePortable" / "App" / "libreoffice" / "program" / "soffice.exe",
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files\LibreOffice 7\program\soffice.exe"),
        Path(r"C:\Program Files\LibreOffice 24\program\soffice.exe"),
    ]
    
    for p in common_paths:
        if p.exists():
            return p

    # Fallback: check if soffice is on the system PATH
    which = shutil.which("soffice") or shutil.which("soffice.exe")
    if which:
        return Path(which)
            
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
    import tempfile
    
    soffice_exe = get_soffice_path()
    
    # On Windows, use soffice.com if it exists to properly capture stdout/stderr
    soffice_com = soffice_exe.with_suffix('.com')
    soffice = soffice_com if soffice_com.exists() else soffice_exe
    
    # Create a temporary directory for the LibreOffice profile.
    # This prevents conflicts with running LibreOffice instances and is
    # required for LibreOffice Portable to run headless without its launcher.
    with tempfile.TemporaryDirectory() as temp_profile_dir:
        # Convert path to file URI format expected by LibreOffice
        profile_uri = Path(temp_profile_dir).as_uri()
        
        args = [
            str(soffice),
            f"-env:UserInstallation={profile_uri}",
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
            raise ConversionError(f"LibreOffice conversion failed: {e.stderr or e.stdout}")
        except Exception as e:
            raise ConversionError(f"Unexpected error running LibreOffice: {e}")
            
        expected = output_dir / f"{input_path.stem}.{target_format}"
        if not expected.exists():
            error_msg = result.stderr or result.stdout or "No output from LibreOffice"
            raise ConversionError(f"Expected output not found: {expected}\nLibreOffice output: {error_msg}")
            
        return expected
