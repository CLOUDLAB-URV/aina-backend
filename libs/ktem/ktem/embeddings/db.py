from typing import Type, TYPE_CHECKING

from ktem.db.engine import engine
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field, Relationship
from theflow.settings import settings as flowsettings
from theflow.utils.modules import import_dotted_string


if TYPE_CHECKING:
    from ktem.db.models import Agent

class BaseEmbeddingTable(SQLModel):
    """Base table to store language model"""

    __abstract__ = True

    name: str = Field(primary_key=True, unique=True)
    spec: dict = Field(default={}, sa_column=Column(JSON))
    default: bool = Field(default=False)


_base_llm: Type[BaseEmbeddingTable] = (
    import_dotted_string(flowsettings.KH_EMBEDDING_LLM, safe=False)
    if hasattr(flowsettings, "KH_EMBEDDING_LLM")
    else BaseEmbeddingTable
)


class EmbeddingTable(_base_llm, table=True):  # type: ignore
    __tablename__ = "embedding"


if not getattr(flowsettings, "KH_ENABLE_ALEMBIC", False):
    EmbeddingTable.metadata.create_all(engine)
