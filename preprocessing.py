import cv2
import os
import fitz  # PyMuPDF to handle PDF reading
import tempfile


def is_image_blurry(image_path: str, threshold: float = 100.0) -> bool:
    """
    Check if the image is blurry based on the Laplacian variance.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise ValueError(f"Error: Could not read the image file '{image_path}'. Please check the path.")

    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
    return laplacian_var < threshold


def preprocess_image_for_ocr(input_image_path: str, output_image_path: str = None, blur_threshold: float = 100.0) -> str:
    """
    Preprocess the image for OCR by converting it to grayscale, blurring, and thresholding.
    Returns the path to the preprocessed image.
    """
    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"Error: The file '{input_image_path}' does not exist.")

    image = cv2.imread(input_image_path)

    if image is None:
        raise ValueError(f"Error: Could not read the image file '{input_image_path}'. Please check the file format.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Otsu's thresholding (binarization)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Apply dilation and erosion to remove small noise and smooth text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)

    if not output_image_path:
        base_name, _ = os.path.splitext(input_image_path)
        output_image_path = f"{base_name}_preprocessed.png"  # Ensure a valid image extension

    print(f"Preprocessed image saved to: {output_image_path}")
    cv2.imwrite(output_image_path, eroded)
    return output_image_path

def create_temp_folder():
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary folder created at {temp_dir}")
    return temp_dir


def pdf_to_images(pdf_path: str, temp_folder: str, resolution_scale: float = 2.0) -> list:
    """
    Convert each page of the PDF to an image and store it in the temp folder.
    The resolution_scale allows control over the image quality.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Error: The PDF file '{pdf_path}' does not exist.")

    pdf_document = fitz.open(pdf_path)
    image_paths = []

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        zoom_matrix = fitz.Matrix(resolution_scale, resolution_scale)
        pix = page.get_pixmap(matrix=zoom_matrix)

        output_image_path = os.path.join(temp_folder, f"page_{page_number + 1}.png")
        pix.save(output_image_path)
        image_paths.append(output_image_path)
        print(f"Saved page {page_number + 1} as image {output_image_path}")

    return image_paths
