from typing import Annotated

from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from api.core.dependencies import get_current_active_user
from api.schemas.auth import UserInfo
from api.schemas.chat import ChatRequest
from api.schemas.exceptions import GenericException
from api.services.chat import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={
        401: {"description": "Unauthorized", "model": GenericException},
        403: {"description": "Forbidden", "model": GenericException},
    },
    dependencies=[
        Depends(get_current_active_user)  # All routes require authentication
    ],
)


@router.post("/{agent_id}/{conversation_id}", response_class=EventSourceResponse)
async def chat_with_agent(
    agent_id: str,
    conversation_id: str,
    request: ChatRequest,
    service: Annotated[ChatService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Send a message to an agent within a specific conversation."""
    return EventSourceResponse(
        service.chat_with_agent(agent_id, conversation_id, current_user.id, request)
    )
