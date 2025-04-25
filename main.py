# external
import uvicorn
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# internal
import clients
from models import ConversionResult
from convertor import handle_conversion


app: FastAPI = FastAPI(lifespan=clients.lifespan)


templates_dir: Path = Path("templates")
static_dir: Path = Path("static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)