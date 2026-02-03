"""Pydantic schemas for YAML catalog serialization."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.schemas.enums import EnrichmentStatus, InferredType


class ColumnMetadataYaml(BaseModel):
    """Column metadata for YAML serialization."""

    path: str = Field(..., min_length=1, description="Full field path (dot notation)")
    name: str = Field(..., min_length=1, description="Field name (last part of path)")
    type: InferredType = Field(..., description="Inferred field type")
    required: bool = Field(..., description="Present in >= 95% of documents")
    nullable: bool = Field(..., description="Can be null")
    enumerable: bool = Field(..., description="Has low cardinality (< 50 values)")
    presence_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Presence ratio (0.0 to 1.0)"
    )
    sample_values: list[Any] = Field(default_factory=list, description="Sample values")
    unique_values: list[Any] | None = Field(
        default=None, description="Unique values if enumerable"
    )
    description: str | None = Field(default=None, description="Manual description")
    enrichment_status: EnrichmentStatus = Field(
        default=EnrichmentStatus.NOT_ENRICHED, description="LLM enrichment status"
    )

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization.

        Returns:
            Dictionary suitable for YAML dumping.
        """
        result: dict[str, Any] = {
            "path": self.path,
            "name": self.name,
            "type": self.type.value,
            "required": self.required,
            "nullable": self.nullable,
            "enumerable": self.enumerable,
            "presence_ratio": self.presence_ratio,
            "sample_values": self.sample_values,
        }
        if self.unique_values is not None:
            result["unique_values"] = self.unique_values
        if self.description is not None:
            result["description"] = self.description
        if self.enrichment_status != EnrichmentStatus.NOT_ENRICHED:
            result["enrichment_status"] = self.enrichment_status.value
        return result

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "ColumnMetadataYaml":
        """Create from parsed YAML dict.

        Args:
            data: Dictionary from YAML parsing.

        Returns:
            ColumnMetadataYaml instance.
        """
        return cls(
            path=data["path"],
            name=data["name"],
            type=InferredType(data["type"]),
            required=data["required"],
            nullable=data["nullable"],
            enumerable=data["enumerable"],
            presence_ratio=data["presence_ratio"],
            sample_values=data.get("sample_values", []),
            unique_values=data.get("unique_values"),
            description=data.get("description"),
            enrichment_status=EnrichmentStatus(
                data.get("enrichment_status", "not_enriched")
            ),
        )


class SourceMetadataYaml(BaseModel):
    """Source metadata for YAML serialization."""

    db_name: str = Field(..., min_length=1, description="Database name")
    table_name: str = Field(..., min_length=1, description="Table/collection name")
    document_count: int = Field(..., ge=0, description="Number of documents sampled")
    extracted_at: datetime = Field(..., description="Extraction timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )
    columns: list[ColumnMetadataYaml] = Field(
        default_factory=list, description="Column metadata list"
    )

    @property
    def source_id(self) -> str:
        """Generate composite source ID.

        Returns:
            Source ID in format db_name.table_name.
        """
        return f"{self.db_name}.{self.table_name}"

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization.

        Returns:
            Dictionary suitable for YAML dumping.
        """
        return {
            "db_name": self.db_name,
            "table_name": self.table_name,
            "document_count": self.document_count,
            "extracted_at": self.extracted_at.isoformat(),
            "updated_at": (self.updated_at or self.extracted_at).isoformat(),
            "columns": [col.to_yaml_dict() for col in self.columns],
        }

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "SourceMetadataYaml":
        """Create from parsed YAML dict.

        Args:
            data: Dictionary from YAML parsing.

        Returns:
            SourceMetadataYaml instance.
        """
        return cls(
            db_name=data["db_name"],
            table_name=data["table_name"],
            document_count=data["document_count"],
            extracted_at=datetime.fromisoformat(data["extracted_at"]),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
            columns=[
                ColumnMetadataYaml.from_yaml_dict(c) for c in data.get("columns", [])
            ],
        )


class IndexEntry(BaseModel):
    """Entry in the catalog index."""

    db_name: str = Field(..., min_length=1, description="Database name")
    table_name: str = Field(..., min_length=1, description="Table/collection name")
    last_extracted: datetime = Field(..., description="Last extraction timestamp")
    file_path: str = Field(..., description="Relative path to YAML file")

    @property
    def source_id(self) -> str:
        """Generate composite source ID.

        Returns:
            Source ID in format db_name.table_name.
        """
        return f"{self.db_name}.{self.table_name}"

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization.

        Returns:
            Dictionary suitable for YAML dumping.
        """
        return {
            "db_name": self.db_name,
            "table_name": self.table_name,
            "last_extracted": self.last_extracted.isoformat(),
            "file_path": self.file_path,
        }

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "IndexEntry":
        """Create from parsed YAML dict.

        Args:
            data: Dictionary from YAML parsing.

        Returns:
            IndexEntry instance.
        """
        return cls(
            db_name=data["db_name"],
            table_name=data["table_name"],
            last_extracted=datetime.fromisoformat(data["last_extracted"]),
            file_path=data["file_path"],
        )


class CatalogIndex(BaseModel):
    """Global catalog index."""

    version: str = Field(default="1.0", description="Index format version")
    generated_at: datetime = Field(..., description="Generation timestamp")
    sources: list[IndexEntry] = Field(
        default_factory=list, description="Indexed sources"
    )

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization.

        Returns:
            Dictionary suitable for YAML dumping.
        """
        return {
            "version": self.version,
            "generated_at": self.generated_at.isoformat(),
            "sources": [s.to_yaml_dict() for s in self.sources],
        }

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "CatalogIndex":
        """Create from parsed YAML dict.

        Args:
            data: Dictionary from YAML parsing.

        Returns:
            CatalogIndex instance.
        """
        return cls(
            version=data.get("version", "1.0"),
            generated_at=datetime.fromisoformat(data["generated_at"]),
            sources=[IndexEntry.from_yaml_dict(s) for s in data.get("sources", [])],
        )

    def find_source(self, db_name: str, table_name: str) -> IndexEntry | None:
        """Find a source entry by database and table name.

        Args:
            db_name: Database name.
            table_name: Table name.

        Returns:
            IndexEntry if found, None otherwise.
        """
        for entry in self.sources:
            if entry.db_name == db_name and entry.table_name == table_name:
                return entry
        return None

    def find_source_by_id(self, source_id: str) -> IndexEntry | None:
        """Find a source entry by composite ID.

        Args:
            source_id: Source ID in format db_name.table_name.

        Returns:
            IndexEntry if found, None otherwise.
        """
        for entry in self.sources:
            if entry.source_id == source_id:
                return entry
        return None
