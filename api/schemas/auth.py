from ktem.db.base_models import Role
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(description="The access token")
    token_type: str = Field(description="The type of the token")


class TokenData(BaseModel):
    username: str | None = Field(
        default=None, description="The username of the token owner"
    )


class UserLogin(BaseModel):
    username: str = Field(description="The username of the user")
    password: str = Field(description="The password of the user")


class UserInfo(BaseModel):
    id: str = Field(description="The ID of the user")
    username: str = Field(description="The username of the user")
    role: Role


class UserCreate(BaseModel):
    username: str = Field(description="The username of the user")
    password: str = Field(description="The password of the user")
    role: Role = Field(default=Role.CHAT_USER, description="The role of the user")
