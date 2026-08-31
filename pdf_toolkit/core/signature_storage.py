import os
import shutil
from pathlib import Path

def get_signatures_dir() -> Path:
    """Returns the persistent signature storage directory, creating it if needed."""
    # Using APPDATA to strictly avoid QStandardPaths/Qt imports in core/
    app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    sig_dir = Path(app_data) / "PDF ToolBox" / "signatures"
    sig_dir.mkdir(parents=True, exist_ok=True)
    return sig_dir

def save_signature(data, name: str) -> Path:
    """
    Saves a signature. 
    'data' can be a file path (str/Path) for uploads, 
    or a GUI object (like QPixmap) that implements a .save(path, format) method for drawn pads.
    """
    out_path = get_signatures_dir() / f"{name}.png"
    
    if isinstance(data, (str, Path)):
        shutil.copy2(data, out_path)
    elif hasattr(data, "save"):
        # Duck-typing allows us to call QPixmap.save() without importing Qt in core
        data.save(str(out_path), "PNG")
    else:
        raise ValueError("Invalid signature data type")
        
    return out_path

def list_signatures() -> list[dict]:
    """Returns a list of dicts with name and path for all saved signatures."""
    sig_dir = get_signatures_dir()
    results = []
    for file in sig_dir.glob("*.png"):
        results.append({"name": file.stem, "path": str(file)})
    return results

def delete_signature(name: str) -> None:
    """Removes a saved signature by name."""
    file = get_signatures_dir() / f"{name}.png"
    if file.exists():
        file.unlink()
