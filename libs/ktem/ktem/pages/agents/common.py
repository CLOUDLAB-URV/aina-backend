from ktem.db.base_models import Role

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
