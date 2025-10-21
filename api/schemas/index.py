from pydantic import BaseModel, Field


class IndexCreate(BaseModel):
    name: str = Field(description="The name of the index")
    index_type: str = Field(description="The type of the index")
    config: dict = Field(description="The configuration of the index")


class IndexInfo(IndexCreate):
    id: int = Field(description="The unique identifier of the index")
