from pydantic import BaseModel, Field


class RerankingBase(BaseModel):
    name: str = Field(description="The name of the reranking model")
    spec: dict[str, str] = Field(description="The specification of the reranking model")
    default: bool = Field(
        default=False, description="Whether this reranking model is the default one"
    )


class RerankingCreate(RerankingBase):
    vendor_name: str = Field(description="The vendor of the reranking model")


class RerankingInfo(RerankingCreate):
    vendor_qualname: str = Field(description="The qualified name of the vendor")
