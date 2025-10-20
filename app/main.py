# external
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid
import os

# internal
import clients
from convertor import handle_conversion, ProcessRequest, ConversionResponse

app: FastAPI = FastAPI()

templates_dir: Path = Path(__file__).parent.joinpath("templates")
templates: Jinja2Templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    if not s3_bucket:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME environment variable not set.")

    file_key = f"{uuid.uuid4()}-{file.filename}"

    try:
        clients.s3_client.upload_fileobj(
            file.file,
            s3_bucket,
            file_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

    try:
        presigned_url = clients.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket, 'Key': file_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate pre-signed URL: {str(e)}")

    return {"url": presigned_url}


@app.post("/api/process", response_model=ConversionResponse)
async def process_file_url(request: ProcessRequest):
    try:
        return await handle_conversion(request.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)