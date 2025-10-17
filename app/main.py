# external
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from vercel_blob import put
from pydantic import BaseModel
import uuid

app: FastAPI = FastAPI()

templates_dir: Path = Path(__file__).parent.joinpath("templates")
templates: Jinja2Templates = Jinja2Templates(directory=templates_dir)

class UploadRequest(BaseModel):
    filename: str

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/upload")
async def upload_file(request: UploadRequest):
    filename = f"{uuid.uuid4()}-{request.filename}"
    blob = put(filename, b'')
    return {"url": blob['url']}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)