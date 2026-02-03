"""WebSocket message schemas for real-time communication.

This module defines the message types for WebSocket streaming
during the interpretation process.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.schemas.interpreter import ErrorResponse, InterpretationResponse, QueryResponse


class WSMessage(BaseModel):
    """Base WebSocket message."""

    type: str = Field(..., description="Message type identifier")
    data: dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.now)


class WSStatusMessage(BaseModel):
    """Status update message during interpretation."""

    type: Literal["status"] = "status"
    data: dict[str, Any] = Field(
        ...,
        description="Status data with 'status' and 'message' keys",
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def create(cls, status: str, message: str) -> "WSStatusMessage":
        """Create a status message."""
        return cls(data={"status": status, "message": message})


class WSChunkMessage(BaseModel):
    """Streaming chunk message from LLM processing."""

    type: Literal["chunk"] = "chunk"
    data: dict[str, Any] = Field(
        ...,
        description="Chunk data with 'content' and 'agent' keys",
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def create(cls, content: str, agent: str) -> "WSChunkMessage":
        """Create a chunk message."""
        return cls(data={"content": content, "agent": agent})


class WSInterpretationMessage(BaseModel):
    """Interpretation result message."""

    type: Literal["interpretation"] = "interpretation"
    data: InterpretationResponse = Field(..., description="Interpretation result")
    timestamp: datetime = Field(default_factory=datetime.now)


class WSQueryMessage(BaseModel):
    """Generated query message."""

    type: Literal["query"] = "query"
    data: QueryResponse = Field(..., description="Generated query")
    timestamp: datetime = Field(default_factory=datetime.now)


class WSErrorMessage(BaseModel):
    """Error message."""

    type: Literal["error"] = "error"
    data: ErrorResponse = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> "WSErrorMessage":
        """Create an error message."""
        return cls(
            data=ErrorResponse(
                code=code,
                message=message,
                details=details,
                suggestions=suggestions or [],
            )
        )


# Type alias for all possible WebSocket messages
WSMessageType = (
    WSStatusMessage
    | WSChunkMessage
    | WSInterpretationMessage
    | WSQueryMessage
    | WSErrorMessage
)
