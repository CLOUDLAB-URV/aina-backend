from typing import Annotated, Any

from fastapi import APIRouter, Depends, UploadFile, status
from sse_starlette import EventSourceResponse

from api.core.dependencies import get_agent_creator_user, get_current_active_user
from api.schemas.auth import UserInfo
from api.schemas.exceptions import GenericException
from api.schemas.index import IndexInfo
from api.services.index import IndexService

router = APIRouter(
    prefix="/index",
    tags=["index"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
    },
)


@router.get(
    "/", response_model=list[IndexInfo], dependencies=[Depends(get_agent_creator_user)]
)
async def list_indices(service: Annotated[IndexService, Depends()]):
    return service.list_indices()


@router.get("/types", dependencies=[Depends(get_agent_creator_user)])
async def list_index_types(
    service: Annotated[IndexService, Depends()],
):
    return service.list_index_types()


@router.get(
    "/index/{index_id}",
    response_model=IndexInfo,
    dependencies=[Depends(get_agent_creator_user)],
)
async def get_index(index_id: int, service: Annotated[IndexService, Depends()]):
    return service.get_index(index_id)


@router.delete("/index/{index_id}", dependencies=[Depends(get_agent_creator_user)])
async def delete_index(index_id: int, service: Annotated[IndexService, Depends()]):
    service.delete_index(index_id)


@router.post(
    "/",
    response_model=IndexInfo,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_agent_creator_user)],
)
async def create_index(
    name: str,
    config: dict,
    index_type: str,
    service: Annotated[IndexService, Depends()],
):
    return service.create_index(name, config, index_type)


@router.get("/index/{index_id}/")
async def list_files(
    index_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
    service: Annotated[IndexService, Depends()],
    name_pattern: str = "",
):
    return service.list_files(current_user.id, index_id, name_pattern)


@router.get("/index/{index_id}/groups")
async def list_groups(
    index_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)],
    service: Annotated[IndexService, Depends()],
):
    return service.list_groups(current_user.id, index_id)


@router.post("/index/{index_id}/index_files", response_class=EventSourceResponse)
async def index_files(
    index_id: int,
    agent_id: str,
    files: list[UploadFile],
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    service: Annotated[IndexService, Depends()],
    reindex: bool = False,
):
    return EventSourceResponse(
        service.index_files(current_user.id, agent_id, index_id, files, reindex)
    )


@router.patch("/index/{index_id}")
async def update_index(
    index_id: int,
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    service: Annotated[IndexService, Depends()],
    config: dict[str, Any] | None = None,
    name: str | None = None,
):
    service.update_index(index_id, name, config)


@router.get("/admin_settings", response_model=dict[str, Any])
async def get_admin_settings(
    index_type: str,
    current_user: Annotated[UserInfo, Depends(get_agent_creator_user)],
    service: Annotated[IndexService, Depends()],
):
    return service.get_admin_settings(index_type)
