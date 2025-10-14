from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.core.config import settings
from api.core.dependencies import get_current_active_user
from api.core.security import create_access_token
from api.schemas.auth import Token, UserResponse
from api.schemas.exceptions import GenericException
from api.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized", "model": GenericException}},
)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends()],
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"Authenticated user: {user.username}, role: {user.role}")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)]
) -> UserResponse:
    """Get current user information."""
    return current_user


# @router.post("/register", response_model=UserResponse)
# async def register_user(
#     user_data: UserCreate,
#     admin_user: Annotated[UserResponse, Depends(get_admin_user)],  # Only admins can create users
#     auth_service: Annotated[AuthService, Depends()]
# ) -> UserResponse:
#     """Register a new user (admin only)."""
#     return auth_service.create_user(user_data)


@router.post("/test-token", response_model=UserResponse)
async def test_token(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)]
) -> UserResponse:
    """Test access token."""
    return current_user
