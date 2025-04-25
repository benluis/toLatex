# external
from enum import Enum
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    openai_api_key: str


class InputType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"


class ConversionResult(BaseModel):
    latex_content: List[str]
    status: str = "success"


class ErrorResponse(BaseModel):
    detail: str
    status: str = "error"