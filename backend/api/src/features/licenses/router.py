from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.config.config import get_backend_config

licenses_router = APIRouter()


@licenses_router.get("/licenses", response_class=PlainTextResponse)
def get_licenses() -> PlainTextResponse:
    config = get_backend_config()
    result = config.licenses_txt_path.read_text(encoding="utf-8")
    return PlainTextResponse(content=result)
