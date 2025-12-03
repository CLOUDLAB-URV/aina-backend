from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SelectMode(Enum):
    ALL = "all"
    SELECT = "select"
    DISABLED = "disabled"


class ChatRequest(BaseModel):
    message: str = Field(description="Message to send")
    reasoning_type: str | None = Field(
        default=None, description="Type of reasoning to use"
    )
    llm_type: str | None = Field(default=None, description="Type of LLM to use")
    use_mind_map: bool | None = Field(
        default=None, description="Whether to use mind map"
    )
    use_citation: bool | None = Field(
        default=None, description="Whether to use citation"
    )
    language: str | None = Field(default=None, description="Language for the response")
    select_mode: SelectMode = Field(
        default=SelectMode.ALL, description="Mode for selecting index files"
    )
    selected_files: list[str] = Field(
        default=[], description="List of selected files for indexing"
    )


class ConversationInfo(BaseModel):
    messages: list[tuple[str, str]] = Field(
        description="List of messages in the conversation as (human, agent) tuples",
    )
    chat_suggestions: list[list[str]] = Field(
        description="List of chat suggestions for the user"
    )
    retrieval_messages: list[str] = Field(
        description="List of retrieval messages used in the conversation",
    )
    plot_history: list[Any] = Field(
        description="History of plots generated during the conversation",
    )
    selected: dict[str, Any] = Field(
        description="List of files selected for the conversation",
    )
    state: dict[str, Any] = Field(
        description="State information for the conversation",
    )
    likes: list[Any] = Field(
        description="List of likes/dislikes for messages in the conversation",
    )
    timestamps: list[Any] = Field(
        description="List of timestamps for messages in the conversation",
    )
