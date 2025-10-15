# built-in
import tempfile
import subprocess
import os

# external
import uvicorn
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

# internal
import clients
from models import ConversionResult, LatexRequest
from convertor import handle_conversion


app: FastAPI = FastAPI(lifespan=clients.lifespan)


templates_dir: Path = Path("templates")
templates: Jinja2Templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def process_form(
    request: Request,
    file: UploadFile = File(...)
) -> HTMLResponse:
    try:
        results: ConversionResult = await handle_conversion(file=file)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "results": results}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)}
        )


@app.post("/render-latex")
async def render_latex(request: LatexRequest):
    """Render LaTeX to PDF and return the PDF file."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tex_file = os.path.join(tmp_dir, "document.tex")
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(request.latex)

            try:
                process = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmp_dir, tex_file],
                    capture_output=True,
                    check=False
                )

                pdf_file = os.path.join(tmp_dir, "document.pdf")
                if os.path.exists(pdf_file):
                    return FileResponse(pdf_file, media_type="application/pdf", filename="latex_output.pdf")
                else:
                    return {"error": "Failed to compile LaTeX", "log": process.stdout.decode('utf-8', errors='replace')}
            except FileNotFoundError:
                return {"error": "LaTeX compiler (pdflatex) not found on this system",
                        "log": "Please install TeX Live or MiKTeX to enable PDF compilation"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)