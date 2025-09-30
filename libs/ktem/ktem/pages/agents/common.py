from ktem.db.engine import engine
from ktem.db.base_models import Role
from ktem.db.models import Agent, User

from sqlmodel import Session, select

def check_user_permissions_write(user, agent):
    """Check if the user has permission to modify the agent"""
    if not user or not agent:
        return False
    if user.role == Role.CHAT_USER:
        return False
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.AGENT_CREATOR:
        if agent.creators.contains(user.id):
            return True
    return False

def check_user_permissions_read(user, agent):
    """Check if the user has permission to view the agent"""
    if not user or not agent:
        return False
    if user.role == Role.CHAT_USER:
        return False
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.AGENT_CREATOR:
        if agent.creators.contains(user.id):
            return True
    return False

def can_create_agent(user):
    """Check if the user can create an agent"""
    if not user:
        return False
    return user.role in [Role.ADMIN, Role.AGENT_CREATOR]

def load_agents(user_id):
    if not user_id:
        return []

    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            return []

        if user.role == Role.ADMIN:
            agents = session.exec(
                select(Agent)
                .order_by(Agent.date_created.desc())
            ).all()
        elif user.role == Role.AGENT_CREATOR:
            agents = session.exec(
                select(Agent)
                .where(Agent.creators.contains([user.id]))
                .order_by(Agent.date_created.desc())
            ).all()
        else:
            return []

        return agents
