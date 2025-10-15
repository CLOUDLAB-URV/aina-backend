from typing import Any

from pydantic import BaseModel, Field


class LlmBase(BaseModel):
    name: str = Field(description="The name of the LLM")
    spec: dict[str, Any] = Field(description="The specification of the LLM")
    default: bool = Field(
        default=False, description="Whether this LLM is the default one"
    )


class LlmCreate(LlmBase):
    vendor_name: str = Field(description="The vendor of the LLM")


class LlmInfo(LlmCreate):
    vendor_qualname: str = Field(description="The qualified name of the vendor")
