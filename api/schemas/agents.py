from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    name: str | None = Field(default=None, description="The name of the agent")
    description: str | None = Field(
        default=None, description="The description of the agent"
    )
    index_id: int | None = Field(
        default=None, description="The ID of the index to be used by the agent"
    )
    model_name: str | None = Field(
        default=None, description="The name of the model to be used by the agent"
    )
