import base64
import os
import shutil
import tempfile
from typing import List
import asyncio

# external
import cv2
from fastapi import UploadFile, HTTPException

# internal
import clients


async def handle_conversion(
        file: UploadFile
) -> ConversionResult:
    """Handle file conversion to LaTeX with automatic file type detection."""
    temp_folder = None
    save_path = None

    try:
        temp_folder = await create_temp_folder()
        file_extension: str = os.path.splitext(file.filename)[1].lower()

        if file_extension in ['.png', '.jpg', '.jpeg']:
            pass
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload an image file (PNG, JPG, or JPEG)."
            )

        save_path = os.path.join(temp_folder, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result: str = await process_image(save_path, temp_folder)
        latex_content: List[str] = [result]

        return ConversionResult(latex_content=latex_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_folder and os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)


async def is_image_blurry(image_path: str, threshold: float = 100.0) -> bool:
    """Check if an image is blurry."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise RuntimeError(f"Could not read image from {image_path}")

        # Convert image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate the Laplacian variance
        laplacian_variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()

        return laplacian_variance < threshold
    except Exception as e:
        raise RuntimeError(f"Error checking image blurriness: {str(e)}")


async def encode_image(image_path: str) -> str:
    """Encode an image file to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to process image: {str(e)}")
