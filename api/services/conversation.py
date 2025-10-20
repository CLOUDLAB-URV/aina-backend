from ktem.db.engine import engine
from ktem.db.models import Agent, Conversation, User
from sqlmodel import Session, or_, select
from theflow.settings import settings as flowsettings

from api.schemas.conversations import ConversationCreate, ConversationUpdate


class ConversationService:
    def __init__(self):
        pass

    def list_conversations(self, user_id: str, agent_id: str):
        # In case user are admin. They can also watch the
        # public conversations
        can_see_public: bool = False
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            result = session.exec(statement).one_or_none()

            if result is not None:
                if flowsettings.KH_USER_CAN_SEE_PUBLIC:
                    can_see_public = (
                        result.username == flowsettings.KH_USER_CAN_SEE_PUBLIC
                    )
                else:
                    can_see_public = True

        with Session(engine) as session:
            # Define condition based on admin-role:
            # - can_see: can see their conversations & public files
            # - can_not_see: only see their conversations
            if can_see_public:
                statement = (
                    select(Conversation)
                    .where(
                        or_(
                            Conversation.user == user_id,
                            Conversation.is_public,
                        )
                    )
                    .where(Conversation.agent_id == agent_id)
                    .order_by(
                        Conversation.is_public.desc(), Conversation.date_created.desc()
                    )
                )
            else:
                statement = (
                    select(Conversation)
                    .where(
                        Conversation.user == user_id,
                        Conversation.agent_id == agent_id,
                    )
                    .order_by(Conversation.date_created.desc())
                )
            return session.exec(statement).all()

    def add_conversation(
        self, user_id: str, conversation: ConversationCreate
    ) -> Conversation:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")
            agent = session.get(Agent, conversation.agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {conversation.agent_id} not found")
            if user not in agent.users:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to use agent {conversation.agent_id}"
                )
            new_conversation = Conversation.model_validate(conversation)
            new_conversation.user = user_id
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            return new_conversation

    def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        with Session(engine) as session:
            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                raise LookupError(f"Conversation with id {conversation_id} not found")
            if conversation.user != user_id:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to delete conversation {conversation_id}"
                )

            session.delete(conversation)
            session.commit()

    def update_conversation(
        self, user_id: str, conversation_id: str, conversation: ConversationUpdate
    ) -> Conversation:
        with Session(engine) as session:
            existing_conversation = session.get(Conversation, conversation_id)
            if existing_conversation is None:
                raise LookupError(f"Conversation with id {conversation_id} not found")
            if existing_conversation.user != user_id:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to update conversation {conversation_id}"
                )

            update_data = conversation.model_dump(exclude_unset=True)
            existing_conversation.sqlmodel_update(update_data)
            session.add(existing_conversation)
            session.commit()
            session.refresh(existing_conversation)
            return existing_conversation
