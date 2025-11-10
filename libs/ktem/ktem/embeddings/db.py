from typing import TYPE_CHECKING, Type

from ktem.db.engine import engine
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel
from theflow.settings import settings as flowsettings
from theflow.utils.modules import import_dotted_string

if TYPE_CHECKING:
    pass


class BaseEmbeddingTable(SQLModel):
    """Base table to store language model"""

    __abstract__ = True

    name: str = Field(primary_key=True, unique=True)
    spec: dict = Field(default={}, sa_column=Column(JSON))
    is_default: bool = Field(default=False)


_base_llm: Type[BaseEmbeddingTable] = (
    import_dotted_string(flowsettings.KH_EMBEDDING_LLM, safe=False)
    if hasattr(flowsettings, "KH_EMBEDDING_LLM")
    else BaseEmbeddingTable
)


class EmbeddingTable(_base_llm, table=True):  # type: ignore
    __tablename__ = "embedding"


if getattr(flowsettings, "KH_USE_DYNAMODB", False) and getattr(
    flowsettings, "KH_MANAGE_DYNAMODB_TABLES", False
):
    from ktem.db.dynamodb import DynamoDBTableManager

    table_manager = DynamoDBTableManager()
    table_manager.create_table_from_sqlalchemy(EmbeddingTable, wait=False)


if not getattr(flowsettings, "KH_ENABLE_ALEMBIC", False):
    EmbeddingTable.metadata.create_all(engine)
