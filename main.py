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

# internal
import clients
from models import ConversionResponse
from convertor import handle_conversion


app: FastAPI = FastAPI(lifespan=clients.lifespan)


templates_dir: Path = Path("templates")
templates: Jinja2Templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/v1/convert", response_model=ConversionResponse)
async def process_form(
    file: UploadFile = File(...)
) -> ConversionResponse:
    return await handle_conversion(file=file)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)