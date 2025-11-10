from typing import Any, Optional

import ktem.db.base_models as base_models
from ktem.db.engine import engine
from ktem.index.models import Index
from ktem.llms.db import LLMTable
from sqlmodel import JSON, Column, Field, Relationship, SQLModel
from theflow.settings import settings
from theflow.utils.modules import import_dotted_string

_base_conv: type[base_models.BaseConversation] = (
    import_dotted_string(settings.KH_TABLE_CONV, safe=False)
    if hasattr(settings, "KH_TABLE_CONV")
    else base_models.BaseConversation
)

_base_user: type[base_models.BaseUser] = (
    import_dotted_string(settings.KH_TABLE_USER, safe=False)
    if hasattr(settings, "KH_TABLE_USER")
    else base_models.BaseUser
)

_base_agent: type[base_models.BaseAgent] = (
    import_dotted_string(settings.KH_TABLE_AGENT, safe=False)
    if hasattr(settings, "KH_TABLE_AGENT")
    else base_models.BaseAgent
)

_base_settings: type[base_models.BaseSettings] = (
    import_dotted_string(settings.KH_TABLE_SETTINGS, safe=False)
    if hasattr(settings, "KH_TABLE_SETTINGS")
    else base_models.BaseSettings
)

_base_issue_report: type[base_models.BaseIssueReport] = (
    import_dotted_string(settings.KH_TABLE_ISSUE_REPORT, safe=False)
    if hasattr(settings, "KH_TABLE_ISSUE_REPORT")
    else base_models.BaseIssueReport
)


class Conversation(_base_conv, table=True):  # type: ignore
    """Conversation record"""

    agent_id: str | None = Field(default=None, foreign_key="agent.id")
    agent: Optional["Agent"] = Relationship(back_populates="conversations")


class UserAgentCreated(SQLModel, table=True):
    """Link table between users and agents they created"""

    __table_args__ = {"extend_existing": True}
    user_id: str | None = Field(
        default=None, foreign_key="usertable.id", primary_key=True
    )
    agent_id: str | None = Field(default=None, foreign_key="agent.id", primary_key=True)


class UserAgentAccessible(SQLModel, table=True):
    """Link table between users and agents they can access"""

    __table_args__ = {"extend_existing": True}
    user_id: str | None = Field(
        default=None, foreign_key="usertable.id", primary_key=True
    )
    agent_id: str | None = Field(default=None, foreign_key="agent.id", primary_key=True)


class User(_base_user, table=True):  # type: ignore
    """User table"""

    __tablename__ = "usertable"  # user is a reserved keyword in some databases
    created_agents: list["Agent"] = Relationship(
        back_populates="creators", link_model=UserAgentCreated
    )
    accessible_agents: list["Agent"] = Relationship(
        back_populates="users", link_model=UserAgentAccessible
    )


class Agent(_base_agent, table=True):  # type: ignore
    """Agent table"""

    creators: list[User] = Relationship(
        back_populates="created_agents", link_model=UserAgentCreated
    )
    users: list[User] = Relationship(
        back_populates="accessible_agents", link_model=UserAgentAccessible
    )

    conversations: list[Conversation] = Relationship(back_populates="agent")

    index_id: Optional[int] = Field(default=None, foreign_key="ktem__index.id")
    index: Optional["Index"] = Relationship(back_populates="agents")

    model_name: Optional[str] = Field(default=None, foreign_key="llm_table.name")
    model: Optional["LLMTable"] = Relationship(back_populates="agents")

    settings: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    reasoning_id: Optional[str] = Field(default=None)
    lang: Optional[str] = Field(default=None)


class Settings(_base_settings, table=True):  # type: ignore
    """Record of settings"""


class IssueReport(_base_issue_report, table=True):  # type: ignore
    """Record of issues"""


if getattr(settings, "KH_USE_DYNAMODB", False) and getattr(
    settings, "KH_MANAGE_DYNAMODB_TABLES", False
):
    from ktem.db.dynamodb import DynamoDBTableManager

    table_manager = DynamoDBTableManager()
    table_manager.create_tables_from_sqlalchemy(
        [
            Conversation,
            User,
            Agent,
            Settings,
            IssueReport,
            UserAgentAccessible,
            UserAgentCreated,
        ],
        wait=False,
    )

if not getattr(settings, "KH_ENABLE_ALEMBIC", False):
    SQLModel.metadata.create_all(engine)
