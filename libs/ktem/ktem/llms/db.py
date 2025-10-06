from typing import TYPE_CHECKING, Type

from ktem.db.engine import engine
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel
from theflow.settings import settings as flowsettings
from theflow.utils.modules import import_dotted_string

if TYPE_CHECKING:
    from ktem.db.models import Agent


class BaseLLMTable(SQLModel):
    """Base table to store language model"""

    __abstract__ = True

    name: str = Field(primary_key=True, unique=True)
    spec: dict = Field(default={}, sa_column=Column(JSON))
    default: bool = Field(default=False)


_base_llm: Type[BaseLLMTable] = (
    import_dotted_string(flowsettings.KH_TABLE_LLM, safe=False)
    if hasattr(flowsettings, "KH_TABLE_LLM")
    else BaseLLMTable
)


class LLMTable(_base_llm, table=True):  # type: ignore
    __tablename__ = "llm_table"
    agents: list["Agent"] = Relationship(back_populates="model")


if not getattr(flowsettings, "KH_ENABLE_ALEMBIC", False):
    LLMTable.metadata.create_all(engine)
