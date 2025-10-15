import datetime

from pydantic import BaseModel, Field


class ConversationInfo(BaseModel):
    id: str = Field(description="The ID of the conversation")
    name: str = Field(description="The name of the conversation")
    user: str = Field(description="The ID of the user who owns the conversation")
    is_public: bool = Field(
        default=False, description="Whether the conversation is public"
    )
    date_created: datetime.datetime = Field(
        description="The creation timestamp of the conversation"
    )
    date_updated: datetime.datetime = Field(
        description="The last update timestamp of the conversation"
    )
    agent_id: str | None = Field(
        default=None, description="The ID of the agent associated with the conversation"
    )


class ConversationCreate(BaseModel):
    name: str = Field(description="The name of the conversation")
    is_public: bool = Field(
        default=False, description="Whether the conversation is public"
    )
    agent_id: str = Field(
        description="The ID of the agent associated with the conversation"
    )
