from typing import Any

from pydantic import BaseModel, Field


class EmbeddingBase(BaseModel):
    name: str = Field(description="The name of the embedding model")
    spec: dict[str, Any] = Field(description="The specification of the embedding model")
    default: bool = Field(
        default=False, description="Whether this embedding model is the default one"
    )


class EmbeddingCreate(EmbeddingBase):
    vendor_name: str = Field(description="The vendor of the embedding model")


class EmbeddingInfo(EmbeddingCreate):
    vendor_qualname: str = Field(description="The qualified name of the vendor")
