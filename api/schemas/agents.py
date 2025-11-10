import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    description: str | None = Field(
        default=None, description="The description of the agent"
    )
    index_id: int | None = Field(
        default=None, description="The ID of the index to be used by the agent"
    )
    reasoning_id: str | None = Field(
        default=None, description="The ID of the reasoning to be used by the agent"
    )


class AgentUpdate(AgentBase):
    name: str | None = Field(default=None, description="The name of the agent")
    settings: dict[str, Any] | None = Field(
        default=None, description="The settings of the agent"
    )


class AgentCreate(AgentBase):
    name: str = Field(description="The name of the agent")


class AgentResponse(AgentCreate):
    id: str = Field(description="The unique identifier of the agent")
    date_created: datetime.datetime = Field(
        description="The date the agent was created"
    )


class AgentUsersAndCreatorsResponse(BaseModel):
    creators: list[str] = Field(
        description="List of the usernames of creators associated with the agent"
    )
    users: list[str] = Field(description="List of usernames associated with the agent")
