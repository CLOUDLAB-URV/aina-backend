from pydantic import BaseModel, Field


class IndexCreate(BaseModel):
    name: str = Field(description="The name of the index")
    index_type: str = Field(description="The type of the index")
    config: dict = Field(description="The configuration of the index")


class IndexInfo(IndexCreate):
    id: int = Field(description="The unique identifier of the index")


class FileInfo(BaseModel):
    id: str = Field(description="The unique identifier of the file")
    name: str = Field(description="The name of the file")
    size: str = Field(description="The size of the file")
    tokens: str = Field(description="The number of tokens in the file")
    loader: str = Field(description="The loader used for the file")
    date_created: str = Field(description="The creation timestamp of the file")


class GroupInfo(BaseModel):
    id: str = Field(description="The unique identifier of the group")
    name: str = Field(description="The name of the group")
    files: list[str] = Field(description="List of file IDs in the group")
    date_created: str = Field(description="The creation timestamp of the group")
