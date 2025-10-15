from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.dependencies import get_current_active_user
from api.schemas.auth import UserInfo
from api.schemas.conversations import (
    ConversationCreate,
    ConversationInfo,
    ConversationUpdate,
)
from api.services.conversation import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "/{agent_id}",
    response_model=list[ConversationInfo],
    response_model_exclude={"data_source"},
)
async def list_conversations(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
    agent_id: str,
    service: Annotated[ConversationService, Depends()],
):
    """List conversations for a given user."""
    return service.list_conversations(current_user.id, agent_id)


@router.post("/")
async def add_conversation(
    conversation: ConversationCreate,
    service: Annotated[ConversationService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Create a new conversation."""
    return service.add_conversation(current_user.id, conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    service: Annotated[ConversationService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Delete a conversation by ID."""
    service.delete_conversation(current_user.id, conversation_id)


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    conversation: ConversationUpdate,
    service: Annotated[ConversationService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Update a conversation by ID."""
    return service.update_conversation(current_user.id, conversation_id, conversation)
