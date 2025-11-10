from typing import TYPE_CHECKING, Optional

from ktem.db.engine import engine
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel
from theflow.settings import settings

if TYPE_CHECKING:
    from ktem.db.models import Agent


# TODO: simplify with using SQLAlchemy directly
class Index(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "ktem__index"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    index_type: str = Field()
    config: dict = Field(default={}, sa_column=Column(JSON))
    agents: list["Agent"] = Relationship(back_populates="index")


if getattr(settings, "KH_USE_DYNAMODB", False) and getattr(
    settings, "KH_MANAGE_DYNAMODB_TABLES", False
):
    from ktem.db.dynamodb import DynamoDBTableManager

    table_manager = DynamoDBTableManager()
    table_manager.create_table_from_sqlalchemy(Index, wait=False)

Index.metadata.create_all(engine)
