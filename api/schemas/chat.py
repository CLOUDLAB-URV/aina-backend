from enum import Enum

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
