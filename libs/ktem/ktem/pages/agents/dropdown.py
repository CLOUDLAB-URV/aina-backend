import gradio as gr
from ktem.app import BasePage
from ktem.db.engine import engine
from ktem.db.models import Agent, User
from ktem.llms.manager import llms
from ktem.embeddings.manager import embedding_models_manager
from sqlmodel import Session, select

from .common import check_user_permissions_write


class AgentSettings(BasePage):
    def __init__(self, app, selected_agent):
        self._app = app
        self.selected_agent = selected_agent
        self.on_building_ui()

    def on_building_ui(self):
        self.index = gr.Dropdown(
            label="Index",
            choices=[],
            interactive=True,
        )
        self.model = gr.Dropdown(
            label="Model",
            choices=[],
            interactive=True,
        )
        self.embedding = gr.Dropdown(
            label="Embedding",
            choices=[],
            interactive=True,
        )

    def _validate_agent_and_user(self, session, user_id, agent_id, action="modify"):
        """
        Validates agent and user existence and permissions.
        
        Args:
            session: Database session
            user_id: User ID
            agent_id: Agent ID  
            action: Action being performed (for error message)
            
        Returns:
            tuple: (agent, user) if validation passes, (None, None) if it fails
        """
        if not agent_id:
            gr.Warning("No agent selected.")
            return None, None

        agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
        if not agent:
            gr.Warning("Agent not found.")
            return None, None

        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            gr.Warning("User not found.")
            return None, None

        if not check_user_permissions_write(user, agent):
            gr.Warning(f"You do not have permission to {action} this agent.")
            return None, None

        return agent, user

    def update_index(self, user_id, agent_id, index_id):
        with Session(engine) as session:
            agent, user = self._validate_agent_and_user(session, user_id, agent_id, "modify")
            if not agent or not user:
                return

            agent.index_id = index_id
            session.add(agent)
            session.commit()

    def update_model(self, user_id, agent_id, model_name):
        with Session(engine) as session:
            agent, user = self._validate_agent_and_user(session, user_id, agent_id, "modify")
            if not agent or not user:
                return

            agent.model_name = model_name
            session.add(agent)
            session.commit()

    def update_embedding(self, user_id, agent_id, embedding_name):
        with Session(engine) as session:
            agent, user = self._validate_agent_and_user(session, user_id, agent_id, "modify")
            if not agent or not user:
                return

            agent.embedding_name = embedding_name
            session.add(agent)
            session.commit()

    def on_agent_change(self, user_id, agent_id):
        empty_response = (
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None)
        )

        with Session(engine) as session:
            agent, user = self._validate_agent_and_user(
                session, user_id, agent_id, "view this agent's settings"
            )
            if not agent or not user:
                return empty_response

            all_indexes = self._app.index_manager.indices
            all_indexes = [(idx.name, idx.id) for idx in all_indexes]
            index_value = agent.index_id if agent.index_id else None

            model_value = agent.model.name if agent.model else None

            embedding_value = agent.embedding.name if agent.embedding else None

            return (
                gr.update(
                    choices=all_indexes,
                    value=index_value
                ),
                gr.update(
                    choices=list(llms.options().keys()),
                    value=model_value
                ),
                gr.update(
                    choices=list(embedding_models_manager.options().keys()),
                    value=embedding_value
                )
            )

    def on_register_events(self):
        self.selected_agent.change(
            fn=self.on_agent_change,
            inputs=[
                self._app.user_id,
                self.selected_agent,
            ],
            outputs=[
                self.index,
                self.model,
                self.embedding
            ],
            show_progress=False,
        )
        self.index.select(
            fn=self.update_index,
            inputs=[
                self._app.user_id,
                self.selected_agent,
                self.index,
            ],
        )
        self.model.select(
            fn=self.update_model,
            inputs=[
                self._app.user_id,
                self.selected_agent,
                self.model,
            ],
        )
        self.embedding.select(
            fn=self.update_embedding,
            inputs=[
                self._app.user_id,
                self.selected_agent,
                self.embedding,
            ],
        )
