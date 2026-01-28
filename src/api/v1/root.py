"""Root endpoint."""

from fastapi import APIRouter

from src.config import get_settings
from src.schemas.root import RootResponse

router = APIRouter(tags=["Root"])


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Get API information."""
    settings = get_settings()
    return RootResponse(
        name="QAUserSearch API",
        version=settings.version,
        docs_url="/docs",
    )
