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
    dependencies=[
        Depends(get_current_active_user)  # All routes require authentication
    ],
    responses={
        401: {"description": "Unauthorized", "model": GenericException},
        403: {"description": "Forbidden", "model": GenericException},
        404: {"description": "Not Found", "model": GenericException},
    },
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


@router.post("/{agent_id}/{conversation_id}/select")
async def select_conversation(
    agent_id: str,
    conversation_id: str,
    service: Annotated[ChatService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Select data sources for a specific conversation."""
    return service.select_conversation(agent_id, conversation_id, current_user.id)


@router.post("/{agent_id}/{conversation_id}/like", response_model=dict)
async def like_message(
    agent_id: str,
    conversation_id: str,
    message_index: int,
    service: Annotated[ChatService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
    liked: bool | str = True,
):
    """Like or dislike a message in a specific conversation."""
    return service.like_message(
        agent_id, conversation_id, current_user.id, message_index, liked
    )
