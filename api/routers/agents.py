from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from api.core.dependencies import get_agent_creator_user, get_current_active_user
from api.schemas.agents import (
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    AgentUsersAndCreatorsResponse,
)
from api.schemas.auth import UserInfo
from api.schemas.exceptions import GenericException
from api.services.agent import AgentService

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        401: {"description": "Unauthorized", "model": GenericException},
        403: {"description": "Forbidden", "model": GenericException},
        404: {"description": "Not Found", "model": GenericException},
    },
    dependencies=[
        Depends(get_current_active_user)  # All routes require authentication
    ],
)


@router.get("/created", response_model=list[AgentResponse])
async def list_agents_created(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
):
    """List agents created by the current user."""
    return service.list_agents_created(current_user.id)


@router.get("/accessible", response_model=list[AgentResponse])
async def list_agents_accessible(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """List agents accessible to the current user."""
    return service.list_agents_accessible(current_user.id)


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def add_agent(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent: AgentCreate,
):
    """Create a new agent."""
    return service.add_agent(current_user.id, agent)


@router.delete("/{agent_id}", response_model=None)
async def delete_agent(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Delete an agent by ID."""
    service.delete_agent(current_user.id, agent_id)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
    agent: AgentUpdate,
):
    """Update an agent by ID."""
    return service.update_agent(current_user.id, agent_id, agent)


@router.get("/{agent_id}/users", response_model=AgentUsersAndCreatorsResponse)
async def get_agent_users_and_creators(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Get users and creators for an agent by ID."""
    return service.get_agent_users_and_creators(current_user.id, agent_id)


@router.post("/{agent_id}/users", response_model=None)
async def update_agent_users_and_creators(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
    users: list[str],
    creators: list[str],
):
    """Update users and creators for an agent by ID."""
    service.update_agent_users_and_creators(current_user.id, agent_id, users, creators)


@router.get("/settings/{agent_id}", response_model=dict[str, Any])
async def get_agent_settings(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Get settings for an agent by ID."""
    return service.get_agent_settings(current_user.id, agent_id)


@router.get("/settings/{agent_id}/current", response_model=dict[str, Any])
async def get_current_agent_settings(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Get current settings for an agent by ID."""
    return service.get_current_settings(current_user.id, agent_id)


@router.patch("/settings/{agent_id}", response_model=None)
async def update_agent_settings(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
    settings: dict[str, Any],
):
    """Update settings for an agent by ID."""
    service.update_agent_settings(current_user.id, agent_id, settings)


@router.get("/settings/{agent_id}/index", response_model=dict[str, Any])
async def get_index_settings(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Get index settings for an agent by ID."""
    return service.get_index_settings(current_user.id, agent_id)


@router.get("/settings/{agent_id}/reasoning", response_model=dict[str, Any])
async def get_reasoning_settings(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
):
    """Get reasoning settings for an agent by ID."""
    return service.get_reasoning_settings(current_user.id, agent_id)
