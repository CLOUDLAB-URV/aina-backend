import gradio as gr
from ktem.app import BasePage
from ktem.db.engine import engine
from ktem.db.models import Agent, User
from sqlmodel import Session, select

from .common import check_user_permissions_write


class AgentUsers(BasePage):
    def __init__(self, app, selected_agent):
        self._app = app
        self.selected_agent = selected_agent
        self.on_building_ui()

    def on_building_ui(self):
        self.creators = gr.Dropdown(
            label="Creators",
            choices=[],
            interactive=True,
            multiselect=True,
        )
        self.users = gr.Dropdown(
            label="Users",
            choices=[],
            interactive=True,
            multiselect=True,
        )

    def on_agent_change(self, user_id, agent_id):
        if not agent_id:
            gr.Warning("No agent selected.")
            return [], []

        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                gr.Warning("Agent not found.")
                return [], []

            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("User not found.")
                return [], []

            if not check_user_permissions_write(user, agent):
                gr.Warning("You do not have permission to view this agent's users.")
                return [], []

            res = session.exec(select(User)).all()
            all_users = [(u.username, u.id) for u in res]
            creators = [u.id for u in agent.creators]
            users = [u.id for u in agent.users]

            return (
                gr.update(choices=all_users, value=creators),
                gr.update(choices=all_users, value=users),
            )

    def update_creators(self, user_id, agent_id, new_creators):
        if not agent_id:
            gr.Warning("No agent selected.")
            return

        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                gr.Warning("Agent not found.")
                return

            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("User not found.")
                return

            if not check_user_permissions_write(user, agent):
                gr.Warning("You do not have permission to modify this agent's users.")
                return

            creators = []
            for u_id in new_creators:
                user = session.exec(select(User).where(User.id == u_id)).first()
                if not user:
                    gr.Warning(f"User with ID {u_id} not found.")
                    continue
                creators.append(user)
            agent.creators = creators
            session.add(agent)
            session.commit()

    def update_users(self, user_id, agent_id, new_users):
        if not agent_id:
            gr.Warning("No agent selected.")
            return

        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                gr.Warning("Agent not found.")
                return

            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("User not found.")
                return

            if not check_user_permissions_write(user, agent):
                gr.Warning("You do not have permission to modify this agent's users.")
                return

            users = []
            for u_id in new_users:
                user = session.exec(select(User).where(User.id == u_id)).first()
                if not user:
                    gr.Warning(f"User with ID {u_id} not found.")
                    continue
                users.append(user)
            agent.users = users
            session.add(agent)
            session.commit()

    def on_register_events(self):
        self.selected_agent.change(
            fn=self.on_agent_change,
            inputs=[
                self._app.user_id,
                self.selected_agent,
            ],
            outputs=[self.creators, self.users],
            show_progress="hidden",
        )
        self.creators.select(
            fn=self.update_creators,
            inputs=[self._app.user_id, self.selected_agent, self.creators],
            show_progress="hidden",
        )
        self.users.select(
            fn=self.update_users,
            inputs=[self._app.user_id, self.selected_agent, self.users],
            show_progress="hidden",
        )
