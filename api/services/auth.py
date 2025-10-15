from fastapi import HTTPException, status
from ktem.db.models import User, engine
from sqlmodel import Session, select

from api.core.security import verify_password
from api.schemas.auth import UserInfo


class AuthService:
    def authenticate_user(self, username: str, password: str) -> UserInfo | None:
        try:
            with Session(engine) as session:
                user = session.exec(
                    select(User).where(
                        User.username_lower == username.lower().strip(),
                    )
                ).first()
                if not user:
                    return None
                if not verify_password(password, user.password):
                    return None

                return UserInfo(
                    id=user.id,
                    username=user.username,
                    role=user.role,
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}",
            ) from e

    def get_user_by_username(self, username: str) -> UserInfo | None:
        try:
            with Session(engine) as session:
                user = session.exec(
                    select(User).where(
                        User.username_lower == username.lower().strip(),
                    )
                ).first()
                if not user:
                    return None
                return UserInfo(
                    id=user.id,
                    username=user.username,
                    role=user.role,
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user: {str(e)}",
            ) from e
