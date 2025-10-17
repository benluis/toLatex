# external
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from vercel_blob import put
import uuid

app: FastAPI = FastAPI()

templates_dir: Path = Path(__file__).parent.joinpath("_templates")
templates: Jinja2Templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}-{file.filename}"
    content = await file.read()
    blob = put(filename, content)
    return {"url": blob['url']}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)