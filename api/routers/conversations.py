from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.core.dependencies import get_current_active_user
from api.schemas.auth import UserInfo
from api.schemas.conversations import (
    ConversationCreate,
    ConversationInfo,
    ConversationUpdate,
)
from api.schemas.exceptions import GenericException
from api.services.conversation import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
        404: {"description": "Not Found", "model": GenericException},
    },
)


@router.get("/{agent_id}", response_model=list[ConversationInfo])
async def list_conversations(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
    agent_id: str,
    service: Annotated[ConversationService, Depends()],
):
    """List conversations for a given user."""
    return service.list_conversations(current_user.id, agent_id)


@router.post("/", response_model=ConversationInfo, status_code=status.HTTP_201_CREATED)
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


@router.patch("/{conversation_id}", response_model=ConversationInfo)
async def update_conversation(
    conversation_id: str,
    conversation: ConversationUpdate,
    service: Annotated[ConversationService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """Update a conversation by ID."""
    return service.update_conversation(current_user.id, conversation_id, conversation)
