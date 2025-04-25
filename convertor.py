# built-in
import base64
import os
import shutil
import tempfile
from typing import List
import asyncio

# external
import cv2
import fitz
from fastapi import UploadFile, HTTPException

# internal
import clients
from models import ConversionResult


async def handle_conversion(
        file: UploadFile
) -> ConversionResult:
    """Handle file conversion to LaTeX with automatic file type detection."""
    temp_folder = None
    save_path = None

    try:
        temp_folder = await create_temp_folder()
        file_extension: str = os.path.splitext(file.filename)[1].lower()

        if file_extension == '.pdf':
            input_type = "pdf"
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            input_type = "image"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload a PDF or image file (PNG, JPG, or JPEG)."
            )

        save_path = os.path.join(temp_folder, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        latex_content: List[str] = []

        if input_type == "pdf":
            latex_content = await process_pdf(save_path, temp_folder)
        else:
            result: str = await process_image(save_path, temp_folder)
            latex_content.append(result)

        return ConversionResult(latex_content=latex_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"The file '{input_image_path}' does not exist")

        loop = asyncio.get_running_loop()

        image = await loop.run_in_executor(None, cv2.imread, input_image_path)
        if image is None:
            raise ValueError(f"Could not read the image file '{input_image_path}'")

        height, width = image.shape[:2]
        max_dimension = 2000
        if max(height, width) > max_dimension:
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


async def pdf_to_images(pdf_path: str, temp_folder: str, resolution_scale: float = 2.0) -> List[str]:
    """Convert PDF pages to images."""
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The PDF file '{pdf_path}' does not exist")

        loop = asyncio.get_running_loop()

        pdf_document = await loop.run_in_executor(None, fitz.open, pdf_path)
        image_paths: List[str] = []

        for page_number in range(len(pdf_document)):
            def process_page(page_num):
                page = pdf_document.load_page(page_num)
                zoom_matrix = fitz.Matrix(resolution_scale, resolution_scale)
                pix = page.get_pixmap(matrix=zoom_matrix)

                output_path = os.path.join(temp_folder, f"page_{page_num + 1}.png")
                pix.save(output_path)
                return output_path

            output_path = await loop.run_in_executor(None, process_page, page_number)
            image_paths.append(output_path)

        return image_paths
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to images: {str(e)}")


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
    """Convert a single image to LaTeX using OpenAI's API."""
    try:
        base64_image = await encode_image(image_path)

        _, ext = os.path.splitext(image_path)
        content_type = "image/jpeg"
        if ext.lower() in ['.png']:
            content_type = "image/png"

        data_uri = f"data:{content_type};base64,{base64_image}"

        response = await clients.openai_client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please generate a complete LaTeX document for this image, "
                                    "including the document structure with \\documentclass, "
                                    "\\begin{document}, and \\end{document}. "
                                    "Ensure that the LaTeX code can be compiled directly."
                                    "Do not write anything else other than the latex code."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )

        content = response.choices[0].message.content

        if content.startswith("```"):
            first_line_end = content.find("\n")
            if first_line_end != -1:
                content = content[first_line_end + 1:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to convert to LaTeX: {str(e)}")

async def process_image(image_path: str, temp_folder: str) -> str:
    """Process a single image and convert it to LaTeX."""
    try:
        preprocessed_image: str = await preprocess_image_for_ocr(image_path, temp_folder)
        return await convert_to_latex(preprocessed_image)
    except Exception as e:
        raise RuntimeError(f"Failed to process image: {str(e)}")


async def process_pdf(pdf_path: str, temp_folder: str) -> List[str]:
    """Process all pages in a PDF and convert them to LaTeX."""
    try:
        image_paths: List[str] = await pdf_to_images(pdf_path, temp_folder)
        latex_content: List[str] = []

        for image_path in image_paths:
            content = await process_image(image_path, temp_folder)
            latex_content.append(content)

        return latex_content
    except Exception as e:
        raise RuntimeError(f"Failed to process PDF: {str(e)}")