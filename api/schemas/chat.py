from pydantic import BaseModel, Field


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
