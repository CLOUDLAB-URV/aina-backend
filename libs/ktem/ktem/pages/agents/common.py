from ktem.db.base_models import Role
from ktem.db.engine import engine
from ktem.db.models import Agent, User
from sqlmodel import Session, or_, select


def has_created(user: User, agent: Agent):
    """Check if the user has permission to modify the agent"""
    if not user or not agent:
        return False
    if user.role == Role.CHAT_USER:
        return False
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.AGENT_CREATOR:
        if user in agent.creators:
            return True
    return False


def has_access(user: User, agent: Agent):
    """Check if the user has access to the agent"""
    if not user or not agent:
        return False
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.AGENT_CREATOR:
        if user in agent.creators or user in agent.users:
            return True
    if user.role == Role.CHAT_USER:
        if user in agent.users:
            return True
    return False


def can_create_agent(user):
    """Check if the user can create an agent"""
    if not user:
        return False
    return user.role in [Role.ADMIN, Role.AGENT_CREATOR]


def load_agents_created(user_id):
    if not user_id:
        return []

    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            return []

        if user.role == Role.ADMIN:
            statement = select(Agent)
        elif user.role == Role.AGENT_CREATOR:
            statement = select(Agent).where(
                Agent.creators.contains(user)  # type: ignore
            )
        else:
            return []

        statement = statement.order_by(Agent.date_created.desc())
        agents = session.exec(statement).all()

        return agents


def load_agents_accessible(user_id):
    if not user_id:
        return []

    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            return []

        if user.role == Role.ADMIN:
            statement = select(Agent)
        elif user.role == Role.AGENT_CREATOR:
            statement = (
                select(Agent)
                .where(
                    or_(
                        Agent.users.contains(user),  # type: ignore
                        Agent.creators.contains(user),  # type: ignore
                    )
                )
                .distinct()
            )
        elif user.role == Role.CHAT_USER:
            statement = select(Agent).where(Agent.users.contains(user))  # type: ignore
        else:
            return []

        statement = statement.order_by(Agent.date_created.desc())
        agents = session.exec(statement).all()

        return agents
