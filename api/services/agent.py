from typing import Any

from ktem.db.engine import engine
from ktem.db.models import Agent, User
from ktem.pages.agents.common import (
    has_created,
    load_agents_accessible,
    load_agents_created,
)
from sqlmodel import Session, select

from api.app import app
from api.core.utils import populate_agent_settings
from api.schemas.agents import AgentCreate, AgentUpdate, AgentUsersAndCreatorsResponse


class AgentService:
    def __init__(self):
        pass

    def list_agents_created(self, user_id: str) -> list[Agent]:
        return load_agents_created(user_id)

    def list_agents_accessible(self, user_id: str) -> list[Agent]:
        return load_agents_accessible(user_id)

    def add_agent(self, user_id: str, agent: AgentCreate) -> Agent:
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if user is None:
                raise LookupError(f"User with id {user_id} not found")

            existing_agent = session.exec(
                select(Agent).where(Agent.name == agent.name)
            ).first()
            if existing_agent is not None:
                raise ValueError(f"Agent with name {agent.name} already exists")

            new_agent = Agent(
                creators=[user],
                users=[user],
                name=agent.name,
                description=agent.description,
                index_id=agent.index_id,
            )
            if agent.reasoning_id:
                new_agent.settings["reasoning.use"] = agent.reasoning_id
            session.add(new_agent)
            session.commit()
            session.refresh(new_agent)
            return new_agent

    def delete_agent(self, user_id: str, agent_id: str):
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to delete agent {agent_id}"
                )

            session.delete(agent)
            session.commit()

    def update_agent(self, user_id: str, agent_id: str, agent: AgentUpdate) -> Agent:
        with Session(engine) as session:
            existing_agent = session.get(Agent, agent_id)
            if existing_agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, existing_agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to update agent {agent_id}"
                )
            agent_data = agent.model_dump(exclude_unset=True)
            existing_agent.sqlmodel_update(agent_data)
            session.add(existing_agent)
            session.commit()
            session.refresh(existing_agent)
            return existing_agent

    def get_agent_users_and_creators(self, user_id: str, agent_id: str):
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access users and creators for agent {agent_id}"
                )
            creators = [creator.username for creator in agent.creators]
            users = [user.username for user in agent.users]
            return AgentUsersAndCreatorsResponse(creators=creators, users=users)

    def update_agent_users_and_creators(
        self, user_id: str, agent_id: str, users: list[str], creators: list[str]
    ):
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to update users and creators for agent {agent_id}"
                )

            new_creators = []
            for creator_username in creators:
                creator = session.exec(
                    select(User).where(User.username == creator_username)
                ).first()
                if creator is None:
                    raise LookupError(
                        f"Creator with username {creator_username} not found"
                    )
                new_creators.append(creator)
            agent.creators = new_creators

            new_users = []
            for user_username in users:
                accessible_user = session.exec(
                    select(User).where(User.username == user_username)
                ).first()
                if accessible_user is None:
                    raise LookupError(f"User with username {user_username} not found")
                new_users.append(accessible_user)
            agent.users = new_users

            session.add(agent)
            session.commit()

    def get_agent_settings(self, user_id: str, agent_id: str) -> dict[str, Any]:
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access settings for agent {agent_id}"
                )
            return agent.settings

    def get_current_settings(self, user_id: str, agent_id: str) -> dict[str, Any]:
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access settings for agent {agent_id}"
                )
            if agent.index_id is None:
                raise LookupError(f"Agent with id {agent_id} has no index assigned")
            index = app.index_manager.info().get(agent.index_id)
            if index is None:
                raise LookupError(f"Index with id {agent.index_id} not found")
            return populate_agent_settings(agent.settings or {}, index)

    def update_agent_settings(
        self, user_id: str, agent_id: str, settings: dict[str, Any]
    ):
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to update settings for agent {agent_id}"
                )
            agent.settings.update(settings)
            session.add(agent)
            session.commit()

    def get_index_settings(self, user_id: str, agent_id: str) -> dict[str, Any]:
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access index settings for agent {agent_id}"
                )
            prefix = f"index.options.{agent.index_id or ''}."
            stripped_settings = {}
            for key, value in agent.settings.items():
                if key.startswith(prefix):
                    stripped_settings[key[len(prefix) :]] = value
            return stripped_settings

    def get_reasoning_settings(self, user_id: str, agent_id: str) -> dict[str, Any]:
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            if not has_created(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access reasoning settings for agent {agent_id}"
                )
            reasoning = agent.settings.get("reasoning.use")
            if not reasoning:
                reasoning = list(app.reasonings.keys())[0]
            prefix = f"reasoning.options.{reasoning}."
            stripped_settings = {}
            for key, value in agent.settings.items():
                if key.startswith(prefix):
                    stripped_settings[key[len(prefix) :]] = value
            return stripped_settings
