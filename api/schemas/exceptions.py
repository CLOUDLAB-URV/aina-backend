from pydantic import BaseModel, Field


class GenericException(BaseModel):
    detail: str = Field(description="A description of the error")
