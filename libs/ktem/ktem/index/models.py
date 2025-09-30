from typing import Optional, TYPE_CHECKING

from ktem.db.engine import engine
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

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

Index.metadata.create_all(engine)
