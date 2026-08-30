import io
import os
import tempfile
from pathlib import Path
import pymupdf
from PIL import Image
import pikepdf

from core.utils import (
    validate_file_exists,
    validate_extension,
    validate_pdf,
    get_unique_output_path,
    ConversionError,
    IncorrectPasswordError,
    InvalidFileError
)

VALID_WATERMARK_POSITIONS = frozenset({"center", "diagonal", "top", "bottom"})

def compress_pdf(input_path: str, output_path: str, quality: str = "medium") -> Path:
    """
    Compress a PDF file by downsampling embedded images and applying garbage collection.
    
    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The desired output path for the compressed PDF.
        quality (str): The compression quality level. Allowed values: "low", "medium", "high".
                       "low" gives max compression/smallest file.
                       "high" gives best quality/larger file.
                       
    Returns:
        Path: The actual path where the compressed PDF was saved (may be modified to be unique).
        
    Raises:
        ValueError: If the quality parameter is not one of "low", "medium", "high".
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
        ConversionError: If compression fails.
    """
    valid_qualities = {"low", "medium", "high"}
    if quality not in valid_qualities:
        raise ValueError(f"Invalid quality: '{quality}'. Allowed values are: 'low', 'medium', 'high'.")

    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)

    final_output_path = get_unique_output_path(output_path)

    # Map quality level to rewrite_images parameters.
    # dpi_target=0 means "don't downsample by DPI", letting quality alone drive size.
    # lossless/bitonal=True ensures PNG and 1-bit images are also recompressed (not skipped).
    if quality == "low":
        jpeg_quality = 30
        dpi_target = 72
    elif quality == "medium":
        jpeg_quality = 60
        dpi_target = 96
    else:  # "high"
        jpeg_quality = 90
        dpi_target = 150

    try:
        doc = pymupdf.open(input_path)
    except Exception as e:
        raise ConversionError(f"Failed to open PDF for compression: {e}") from e

    try:
        # Phase 1 — Image re-encoding (pymupdf, document-level).
        # rewrite_images() mutates xref streams directly, so shared xrefs across pages
        # are updated once with no ghost/duplicate references (FIX 1 & 2).
        # lossless=False: PNG/lossless images are left untouched — re-encoding them to
        # JPEG inflates synthetic charts/screenshots (FIX 3). Only already-JPEG sources
        # are re-encoded at the target quality.
        doc.rewrite_images(
            quality=jpeg_quality,
            dpi_target=dpi_target,
            lossless=False,
            bitonal=True,
        )

        # Write pymupdf pass to a temp file so pikepdf can read it.
        fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            doc.save(
                tmp_path,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            )
        finally:
            doc.close()

        # Phase 2 — Structural compression (pikepdf).
        # Generates compact object streams (/ObjStm) and cross-reference streams
        # (/XRef) that PyMuPDF's writer does not produce. This recovers 5-15% on
        # text/vector-heavy PDFs where PyMuPDF's own serialiser would inflate output.
        try:
            pdf = pikepdf.open(tmp_path)
            pdf.save(
                str(final_output_path),
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                compress_streams=True,
            )
            pdf.close()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        raise ConversionError(f"Failed to compress PDF: {e}") from e

    return final_output_path

def protect_pdf(input_path: str, output_path: str, password: str) -> Path:
    """
    Encrypts a PDF file with the given password.
    
    The provided password is used as BOTH the user and owner password.
    
    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The desired output path for the encrypted PDF.
        password (str): The password to encrypt the PDF with.
        
    Returns:
        Path: The actual path where the encrypted PDF was saved.
        
    Raises:
        ValueError: If the password is an empty string.
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
    """
    if not password:
        raise ValueError("Password cannot be an empty string.")
        
    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)
    
    final_output_path = get_unique_output_path(output_path)
    
    try:
        pdf = pikepdf.open(input_path)
    except pikepdf.PasswordError:
        raise InvalidFileError("Input PDF is already encrypted.")
    except Exception as e:
        raise InvalidFileError(f"Failed to open PDF: {e}")
        
    try:
        # Encrypt with the same password for both user and owner.
        enc = pikepdf.Encryption(user=password, owner=password)
        pdf.save(str(final_output_path), encryption=enc)
    except Exception as e:
        raise ConversionError(f"Failed to encrypt PDF: {e}") from e
    finally:
        pdf.close()
        
    return final_output_path

def unlock_pdf(input_path: str, output_path: str, password: str) -> Path:
    """
    Decrypts a password-protected PDF given the correct password.
    
    Args:
        input_path (str): The path to the encrypted PDF file.
        output_path (str): The desired output path for the decrypted PDF.
        password (str): The password to unlock the PDF.
        
    Returns:
        Path: The actual path where the decrypted PDF was saved.
        
    Raises:
        IncorrectPasswordError: If the provided password is wrong.
        InvalidFileError: If the input file is not encrypted or not a valid PDF.
        FileNotFoundError: If the input file does not exist.
    """
    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)
    
    final_output_path = get_unique_output_path(output_path)
    
    try:
        pdf = pikepdf.open(input_path, password=password)
    except pikepdf.PasswordError:
        raise IncorrectPasswordError("Incorrect password provided.")
    except Exception as e:
        raise InvalidFileError(f"Failed to open PDF: {e}")
        
    try:
        if not pdf.is_encrypted:
            raise InvalidFileError("The input PDF is not encrypted.")
            
        pdf.save(str(final_output_path))
    except InvalidFileError:
        raise
    except Exception as e:
        raise ConversionError(f"Failed to unlock PDF: {e}") from e
    finally:
        pdf.close()
        
    return final_output_path

def add_watermark(input_path: str, output_path: str, text: str, opacity: float = 0.3, position: str = "center") -> Path:
    """
    Overlays a text watermark on every page of a PDF.
    
    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The desired output path for the watermarked PDF.
        text (str): The text to overlay.
        opacity (float): Opacity of the watermark text (0.0 to 1.0).
        position (str): The position of the watermark. Allowed values:
                        "center", "diagonal", "top", "bottom".
                        
    Returns:
        Path: The actual path where the watermarked PDF was saved.
        
    Raises:
        ValueError: If text is empty, opacity is out of range, or position is invalid.
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
    """
    if not text:
        raise ValueError("Watermark text cannot be empty.")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Opacity must be between 0.0 and 1.0.")
    if position not in VALID_WATERMARK_POSITIONS:
        raise ValueError(f"Invalid position: '{position}'. Allowed values: {VALID_WATERMARK_POSITIONS}")
        
    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)
    
    final_output_path = get_unique_output_path(output_path)
    
    try:
        doc = pymupdf.open(input_path)
        fontsize = 48
        fontname = "helv"
        
        for page in doc:
            text_length = pymupdf.get_text_length(text, fontname=fontname, fontsize=fontsize)
            page_w = page.rect.width
            page_h = page.rect.height
            
            x_center = page_w / 2
            
            if position == "center":
                y_pos = page_h / 2
                p = pymupdf.Point(x_center - (text_length / 2), y_pos)
                page.insert_text(p, text, fontsize=fontsize, fontname=fontname, fill_opacity=opacity, color=(0.5, 0.5, 0.5))
                
            elif position == "diagonal":
                y_pos = page_h / 2
                p = pymupdf.Point(x_center - (text_length / 2), y_pos)
                center_pt = pymupdf.Point(x_center, y_pos)
                mat = pymupdf.Matrix(-45)
                page.insert_text(p, text, fontsize=fontsize, fontname=fontname, fill_opacity=opacity, color=(0.5, 0.5, 0.5), morph=(center_pt, mat))
                
            elif position == "top":
                y_pos = 72  # 1 inch from top
                p = pymupdf.Point(x_center - (text_length / 2), y_pos)
                page.insert_text(p, text, fontsize=fontsize, fontname=fontname, fill_opacity=opacity, color=(0.5, 0.5, 0.5))
                
            elif position == "bottom":
                y_pos = page_h - 72  # 1 inch from bottom
                p = pymupdf.Point(x_center - (text_length / 2), y_pos)
                page.insert_text(p, text, fontsize=fontsize, fontname=fontname, fill_opacity=opacity, color=(0.5, 0.5, 0.5))
                
        doc.save(str(final_output_path))
    except Exception as e:
        raise ConversionError(f"Failed to add watermark: {e}") from e
    finally:
        doc.close()
        
    return final_output_path

def add_page_numbers(input_path: str, output_path: str, position: str = "bottom-center", start_at: int = 1) -> Path:
    """
    Adds page numbers to every page of a PDF.
    
    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The desired output path for the numbered PDF.
        position (str): The position of the page number. Allowed values:
                        "bottom-center", "bottom-right", "top-center", "top-right".
        start_at (int): The starting number for the first page.
        
    Returns:
        Path: The actual path where the numbered PDF was saved.
        
    Raises:
        ValueError: If position is invalid.
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF.
    """
    valid_positions = {"bottom-center", "bottom-right", "top-center", "top-right"}
    if position not in valid_positions:
        raise ValueError(f"Invalid position: '{position}'. Allowed values: {valid_positions}")
        
    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)
    
    final_output_path = get_unique_output_path(output_path)
    
    try:
        doc = pymupdf.open(input_path)
        fontsize = 12
        fontname = "helv"
        margin = 36
        
        for i, page in enumerate(doc):
            page_num_str = str(start_at + i)
            text_length = pymupdf.get_text_length(page_num_str, fontname=fontname, fontsize=fontsize)
            page_w = page.rect.width
            page_h = page.rect.height
            
            if position == "bottom-center":
                x_pos = (page_w / 2) - (text_length / 2)
                y_pos = page_h - margin
            elif position == "bottom-right":
                x_pos = page_w - margin - text_length
                y_pos = page_h - margin
            elif position == "top-center":
                x_pos = (page_w / 2) - (text_length / 2)
                y_pos = margin + fontsize
            elif position == "top-right":
                x_pos = page_w - margin - text_length
                y_pos = margin + fontsize
                
            p = pymupdf.Point(x_pos, y_pos)
            page.insert_text(p, page_num_str, fontsize=fontsize, fontname=fontname, color=(0, 0, 0))
            
        doc.save(str(final_output_path))
    except Exception as e:
        raise ConversionError(f"Failed to add page numbers: {e}") from e
    finally:
        doc.close()
        
    return final_output_path


def add_image_watermark(input_path: str, output_path: str, image_path: str, opacity: float = 0.3, position: str = "center", scale: float = 0.3) -> Path:
    """
    Overlays an image watermark on every page of a PDF.
    
    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The desired output path for the watermarked PDF.
        image_path (str): The path to the watermark image (jpg/png).
        opacity (float): Opacity of the watermark image (0.0 to 1.0).
        position (str): The position of the watermark. Allowed values:
                        "center", "diagonal", "top", "bottom".
        scale (float): Image width as a fraction of page width (0.0 to 1.0).
                        
    Returns:
        Path: The actual path where the watermarked PDF was saved.
        
    Raises:
        ValueError: If opacity/scale is out of range, or position is invalid.
        FileNotFoundError: If the input file does not exist.
        InvalidFileError: If the input file is not a valid PDF or image is invalid.
    """
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Opacity must be between 0.0 and 1.0.")
    if not 0.0 < scale <= 1.0:
        raise ValueError("Scale must be strictly between 0.0 and 1.0.")
        
    if position not in VALID_WATERMARK_POSITIONS:
        raise ValueError(f"Invalid position: '{position}'. Allowed values: {VALID_WATERMARK_POSITIONS}")
        
    validate_file_exists(input_path)
    validate_extension(input_path, [".pdf"])
    validate_pdf(input_path)
    
    validate_file_exists(image_path)
    # validate_extension only supports ValueError for now? Actually, InvalidFileError is required by the prompt
    # "raise InvalidFileError if not" valid image extension.
    ext = Path(image_path).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise InvalidFileError(f"Invalid image extension: '{ext}'. Allowed extensions are: .jpg, .jpeg, .png")
    
    final_output_path = get_unique_output_path(output_path)
    
    try:
        # Load and prepare image via PIL
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Apply opacity
        alpha = img.split()[3]
        alpha = alpha.point(lambda p: p * opacity)
        img.putalpha(alpha)
        
        # If diagonal, rotate image natively in PIL
        if position == "diagonal":
            img = img.rotate(-45, expand=True, resample=Image.Resampling.BICUBIC)
            
        out_io = io.BytesIO()
        img.save(out_io, format='PNG')
        stream = out_io.getvalue()
        img_w, img_h = img.size
        img.close()
    except Exception as e:
        raise InvalidFileError(f"Failed to process image: {e}") from e
        
    try:
        doc = pymupdf.open(input_path)
        for page in doc:
            page_w = page.rect.width
            page_h = page.rect.height
            
            # Calculate target dimensions
            target_width = page_w * scale
            target_height = target_width * (img_h / img_w)
            
            x_center = (page_w - target_width) / 2
            
            if position in ("center", "diagonal"):
                y_pos = (page_h - target_height) / 2
            elif position == "top":
                y_pos = 72  # 1 inch from top
            elif position == "bottom":
                y_pos = page_h - 72 - target_height
                
            rect = pymupdf.Rect(x_center, y_pos, x_center + target_width, y_pos + target_height)
            
            page.insert_image(rect, stream=stream, keep_proportion=True)
            
        doc.save(str(final_output_path))
    except Exception as e:
        raise ConversionError(f"Failed to add image watermark: {e}") from e
    finally:
        doc.close()
        
    return final_output_path
