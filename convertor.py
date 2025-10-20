import base64
import os
import shutil
import tempfile
from typing import List
import asyncio
from urllib.parse import urlparse

# external
import cv2
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel
import httpx
import google.generativeai as genai
from PIL import Image

# internal
import clients

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class ConversionResponse(BaseModel):
    latex_content: List[str]

class ProcessRequest(BaseModel):
    url: str


async def handle_conversion(file_url: str) -> ConversionResponse:
    temp_folder = None
    try:
        print("Starting handle_conversion...")
        temp_folder = await create_temp_folder()
        print(f"Created temp folder: {temp_folder}")
        
        async with httpx.AsyncClient() as client:
            print(f"Downloading file from: {file_url}")
            response = await client.get(file_url)
            response.raise_for_status()
            print("File downloaded successfully.")
            
            file_content = response.content
            filename = os.path.basename(urlparse(file_url).path)
            save_path = os.path.join(temp_folder, filename)
            
            with open(save_path, "wb") as f:
                f.write(file_content)
            print(f"File saved to: {save_path}")

        file_extension: str = os.path.splitext(filename)[1].lower()

        if file_extension not in ['.png', '.jpg', '.jpeg']:
            raise ValueError(f"Invalid file format: {file_extension}. Only images are supported.")

        print("Processing image...")
        result = await process_image(save_path, temp_folder)
        print("Image processed successfully.")
        latex_content = [result]

        print("Conversion successful.")
        return ConversionResponse(latex_content=latex_content)
    finally:
        if temp_folder and os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)


async def is_image_blurry(image_path: str, threshold: float = 100.0) -> bool:
    """Check if the image is blurry based on the Laplacian variance."""
    try:
        # Use run_in_executor for CPU-bound operations
        loop = asyncio.get_running_loop()
        image = await loop.run_in_executor(
            None, cv2.imread, image_path, cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            raise ValueError(f"Could not read the image file '{image_path}'")

        laplacian_var = await loop.run_in_executor(
            None, lambda: cv2.Laplacian(image, cv2.CV_64F).var()
        )

        return laplacian_var < threshold
    except Exception as e:
        raise RuntimeError(f"Error checking image blur: {str(e)}")


async def preprocess_image_for_ocr(input_image_path: str, output_dir: str) -> str:
    """Minimal preprocessing for better OCR text readability."""
    try:
        print("Starting image preprocessing...")
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"The file '{input_image_path}' does not exist")

        loop = asyncio.get_running_loop()

        image = await loop.run_in_executor(None, cv2.imread, input_image_path)
        if image is None:
            raise ValueError(f"Could not read the image file '{input_image_path}'")

        height, width = image.shape[:2]
        max_dimension = 2000
        if max(height, width) > max_dimension:
            print("Resizing image...")
            scale = max_dimension / max(height, width)
            image = await loop.run_in_executor(
                None,
                lambda: cv2.resize(image, (int(width * scale), int(height * scale)))
            )

        base_name = os.path.basename(input_image_path)
        output_image_path = os.path.join(output_dir, f"processed_{base_name}")

        await loop.run_in_executor(
            None,
            lambda: cv2.imwrite(output_image_path, image, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        )
        print(f"Preprocessed image saved to: {output_image_path}")

        return output_image_path
    except Exception as e:
        raise RuntimeError(f"Error preprocessing image: {str(e)}")


async def create_temp_folder() -> str:
    """Create a temporary folder."""
    try:
        loop = asyncio.get_running_loop()
        temp_dir = await loop.run_in_executor(None, tempfile.mkdtemp)
        return temp_dir
    except Exception as e:
        raise RuntimeError(f"Error creating temporary folder: {str(e)}")


async def encode_image(image_path: str) -> str:
    """Encode an image file to base64 string."""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        def read_and_encode():
            with open(image_path, "rb") as image_file:
                file_content = image_file.read()
                if not file_content:
                    raise ValueError(f"Image file is empty: {image_path}")
                return base64.b64encode(file_content).decode('utf-8')

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, read_and_encode)
    except Exception as e:
        raise RuntimeError(f"Failed to encode image: {str(e)}")


async def convert_to_latex(image_path: str) -> str:
    """Convert a single image to LaTeX using the Gemini API."""
    try:
        print("Opening image for Gemini...")
        img = Image.open(image_path)
        
        model = genai.GenerativeModel('gemini-2.5-flash-lite')

        print("Calling Gemini API...")
        response = await model.generate_content_async([
            "Generate a complete LaTeX document for this image. Only output the LaTeX code.",
            img
        ])
        
        print("Gemini API call successful.")

        content = response.text

        if content.strip().startswith("```"):
            content = content.strip()[content.find("\n") + 1:]

        if content.strip().endswith("```"):
            content = content.strip()[:-3]

        return content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to convert to LaTeX with Gemini: {str(e)}")


async def process_image(image_path: str, temp_folder: str) -> str:
    """Process a single image and convert it to LaTeX."""
    try:
        preprocessed_image: str = await preprocess_image_for_ocr(image_path, temp_folder)
        return await convert_to_latex(preprocessed_image)
    except Exception as e:
        raise RuntimeError(f"Failed to process image: {str(e)}")
