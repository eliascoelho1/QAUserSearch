"""WebSocket message schemas for real-time communication.

This module defines the message types for WebSocket streaming
during the interpretation process.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.schemas.interpreter import ErrorResponse, InterpretationResponse, QueryResponse


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(UTC)


def get_confidence_label(confidence: float) -> str:
    """Get a human-readable label for confidence score.

    Args:
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Human-readable label in Portuguese.
    """
    if confidence >= 0.9:
        return "muito alta"
    elif confidence >= 0.7:
        return "alta"
    elif confidence >= 0.5:
        return "média"
    elif confidence >= 0.3:
        return "baixa"
    else:
        return "muito baixa"


def get_confidence_description(confidence: float) -> str:
    """Get a descriptive message about the confidence level.

    Args:
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Descriptive message in Portuguese.
    """
    if confidence >= 0.9:
        return "Interpretação muito clara - todos os termos foram reconhecidos"
    elif confidence >= 0.7:
        return "Boa interpretação - alguns termos podem ter múltiplos significados"
    elif confidence >= 0.5:
        return (
            "Interpretação parcial - alguns termos não foram completamente reconhecidos"
        )
    elif confidence >= 0.3:
        return "Interpretação incerta - considere reformular o prompt"
    else:
        return "Interpretação muito incerta - recomendamos reformular o prompt com termos mais específicos"


class WSMessage(BaseModel):
    """Base WebSocket message."""

    type: str = Field(..., description="Message type identifier")
    data: dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=_utc_now)


class WSStatusMessage(BaseModel):
    """Status update message during interpretation."""

    type: Literal["status"] = "status"
    data: dict[str, Any] = Field(
        ...,
        description="Status data with 'status' and 'message' keys",
    )
    timestamp: datetime = Field(default_factory=_utc_now)

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
    timestamp: datetime = Field(default_factory=_utc_now)

    @classmethod
    def create(cls, content: str, agent: str) -> "WSChunkMessage":
        """Create a chunk message."""
        return cls(data={"content": content, "agent": agent})


class WSInterpretationMessage(BaseModel):
    """Interpretation result message."""

    type: Literal["interpretation"] = "interpretation"
    data: InterpretationResponse = Field(..., description="Interpretation result")
    timestamp: datetime = Field(default_factory=_utc_now)

    @classmethod
    def create_with_confidence_info(
        cls, interpretation: InterpretationResponse
    ) -> "WSInterpretationMessage":
        """Create an interpretation message with confidence metadata.

        The returned message includes the confidence score along with
        human-readable labels and descriptions.
        """
        return cls(data=interpretation)

    def get_confidence_info(self) -> dict[str, Any]:
        """Get confidence information for display.

        Returns:
            Dictionary with confidence score, label, and description.
        """
        return {
            "score": self.data.confidence,
            "percentage": f"{int(self.data.confidence * 100)}%",
            "label": get_confidence_label(self.data.confidence),
            "description": get_confidence_description(self.data.confidence),
        }


class WSQueryMessage(BaseModel):
    """Generated query message."""

    type: Literal["query"] = "query"
    data: QueryResponse = Field(..., description="Generated query")
    timestamp: datetime = Field(default_factory=_utc_now)


class WSErrorMessage(BaseModel):
    """Error message."""

    type: Literal["error"] = "error"
    data: ErrorResponse = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=_utc_now)

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
