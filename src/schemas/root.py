"""Root endpoint schemas."""

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Root endpoint response."""

    name: str = Field(description="API name")
    version: str = Field(description="API version")
    docs_url: str = Field(description="Documentation URL")
