# LaTeX Generator

A web application that converts images and PDFs containing equations, formulas, or mathematical content into compilable LaTeX code using OpenAI's GPT-4o model.

## Features

- Convert images (PNG, JPG, JPEG) to LaTeX
- Convert multi-page PDFs to LaTeX (one LaTeX document per page)
- Clean temporary files automatically
- Simple, user-friendly interface
- Copy LaTeX code to clipboard with one click

## Prerequisites

- Python 3.8+
- OpenAI API key

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd latex-generator
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

1. Start the application:

```bash
python main.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Upload an image or PDF file containing mathematical content

4. Click "Generate LaTeX" to convert the content

5. Copy the generated LaTeX code using the "Copy Code" button

## Project Structure

- `main.py`: FastAPI application entry point
- `convertor.py`: Image/PDF processing and LaTeX conversion
- `clients.py`: OpenAI client initialization
- `models.py`: Pydantic data models
- `templates/`: HTML templates for the web interface

## License

[MIT License](LICENSE)

## Acknowledgements

- OpenAI for the GPT-4o API
- FastAPI for the web framework
- PyMuPDF for PDF handling
- OpenCV for image processing
