from typing import Annotated

from fastapi import APIRouter, Depends, status
from ktem.db.models import Agent

from api.core.dependencies import get_agent_creator_user, get_current_active_user
from api.schemas.agents import AgentInfo
from api.schemas.auth import UserInfo
from api.schemas.exceptions import GenericException
from api.services.agent import AgentService

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        401: {"description": "Unauthorized", "model": GenericException},
        403: {"description": "Forbidden", "model": GenericException},
    },
    dependencies=[
        Depends(get_current_active_user)  # All routes require authentication
    ],
)


@router.get("/created", response_model=list[Agent])
async def list_agents_created(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """List agents created by the current user."""
    return service.list_agents_created(current_user.id)


@router.get("/accessible", response_model=list[Agent])
async def list_agents_accessible(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
):
    """List agents accessible to the current user."""
    return service.list_agents_accessible(current_user.id)


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def add_agent(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent: AgentInfo,
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


@router.patch("/{agent_id}", response_model=Agent)
async def update_agent(
    service: Annotated[AgentService, Depends()],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    agent_id: str,
    agent: AgentInfo,
):
    """Update an agent by ID."""
    return service.update_agent(current_user.id, agent_id, agent)
