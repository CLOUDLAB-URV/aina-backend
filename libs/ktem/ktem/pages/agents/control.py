import logging
import os

import gradio as gr
from ktem.app import BasePage
from ktem.db.engine import engine
from ktem.db.models import Agent, User
from ktem.db.base_models import Role
from sqlmodel import Session, select

from .common import (
    check_user_permissions_write,
    check_user_permissions_read,
    can_create_agent,
    load_agents_created,
)

logger = logging.getLogger(__name__)

ASSETS_DIR = "assets/icons"
if not os.path.isdir(ASSETS_DIR):
    ASSETS_DIR = "libs/ktem/ktem/assets/icons"


class AgentControl(BasePage):
    def __init__(self, app, selected_agent):
        self._app = app
        self.selected_agent = selected_agent
        self.on_building_ui()

    def on_building_ui(self):
        self.agent_dropdown = gr.Dropdown(
            label="Select Agent",
            choices=[],
            container=False,
            filterable=True,
            interactive=True,
            elem_classes=["unset-overflow"],
        )
        with gr.Row() as self._new_delete:
            self.btn_agent_rn = gr.Button(
                value="",
                icon=f"{ASSETS_DIR}/rename.svg",
                min_width=2,
                scale=1,
                size="sm",
                elem_classes=["no-background", "body-text-color"],
            )
            self.btn_del = gr.Button(
                value="",
                icon=f"{ASSETS_DIR}/delete.svg",
                min_width=2,
                scale=1,
                size="sm",
                elem_classes=["no-background", "body-text-color"],
            )
            self.btn_new = gr.Button(
                value="",
                icon=f"{ASSETS_DIR}/new.svg",
                min_width=2,
                scale=1,
                size="sm",
                elem_classes=["no-background", "body-text-color"],
                # elem_id="new-conv-button",
            )
        with gr.Row(visible=False) as self._delete_confirm:
            self.btn_del_conf = gr.Button(
                value="Delete",
                variant="stop",
                min_width=10,
            )
            self.btn_del_cnl = gr.Button(value="Cancel", min_width=10)
        with gr.Row():
            self.agent_rn = gr.Textbox(
                label="(Enter) to save",
                placeholder="Agent name",
                container=True,
                scale=5,
                min_width=10,
                interactive=True,
                visible=False,
            )
        with gr.Row():
            self.agent_new = gr.Textbox(
                label="(Enter) to create",
                placeholder="New agent name",
                container=True,
                scale=5,
                min_width=10,
                interactive=True,
                visible=False,
            )

    def refresh_agent_list(self, user_id):
        agents = load_agents_created(user_id)
        agents = [(a.name, a.id) for a in agents]
        return gr.update(choices=agents)

    def select_agent(self, user_id, agent_id):
        if not user_id:
            gr.Warning("You must be signed in to select an agent.")
            return gr.update(value=None), None, ""
        if not agent_id:
            # gr.Warning("No agent selected.")
            return gr.update(value=None), None, ""

        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("No user found.")
                return gr.update(value=None), None, ""
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                gr.Warning("No agent found.")
                return gr.update(value=None), None, ""
            if not check_user_permissions_read(user, agent):
                gr.Warning("You do not have permission to view this agent.")
                return gr.update(value=None), None, ""
            logger.info("Selected agent: %s (ID: %s)", agent.name, agent.id)
            return gr.update(value=agent.id), agent.id, agent.name

    def new_agent(self, user_id, agent_name):
        agent_dropdown = gr.update(choices=[], value=None)
        agent_id = None
        agent_rn = ""

        if not user_id:
            gr.Warning("You must be signed in to create an agent.")
            return agent_dropdown, agent_id, agent_rn
        if not agent_name:
            errors = self.is_valid_agent_name(agent_name)
            if errors:
                gr.Warning(errors)
                return agent_dropdown, agent_id, agent_rn
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("You must be signed in to create an agent.")
                return agent_dropdown, agent_id, agent_rn
            if not can_create_agent(user):
                gr.Warning("You do not have permission to create an agent.")
                return agent_dropdown, agent_id, agent_rn
            existing_agent = session.exec(
                select(Agent).where(Agent.name == agent_name)
            ).first()
            if existing_agent:
                gr.Warning("An agent with this name already exists.")
                return agent_dropdown, agent_id, agent_rn
            new_agent = Agent(
                name=agent_name,
                creators=[user],
                users=[user],
            )
            session.add(new_agent)
            session.commit()
            agent_id = new_agent.id

        agents = load_agents_created(user_id)
        agents = [(agent.name, agent.id) for agent in agents]
        return gr.update(choices=agents, value=agent_id), agent_id, agent_name

    def delete_agent(self, user_id, agent_id):
        if not user_id:
            gr.Warning("You must be signed in to delete an agent.")
            return gr.update(), None
        if not agent_id:
            gr.Warning("No agent selected.")
            return gr.update(), None
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("You must be signed in to delete an agent.")
                return gr.update(visible=False), gr.update(choices=[], value=None)
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                gr.Warning("Agent not found.")
                return gr.update(visible=False), gr.update(choices=[], value=None)
            if not check_user_permissions_write(user, agent):
                gr.Warning("You do not have permission to delete this agent.")
                return gr.update(visible=False), gr.update(choices=[], value=None)
            session.delete(agent)
            session.commit()

        agents = load_agents_created(user_id)
        agents = [(agent.name, agent.id) for agent in agents]
        return gr.update(choices=agents, value=None), None

    def rename_agent(self, user_id, agent_id, new_name):
        if not user_id:
            gr.Warning("You must be signed in to rename an agent.")
            return gr.update(value=None), gr.update(visible=False)
        if not agent_id:
            gr.Warning("No agent selected.")
            return gr.update(value=None), gr.update(visible=False)
        if not new_name:
            gr.Warning("Agent name cannot be empty.")
            return gr.update(value=None), gr.update(visible=False)
        errors = self.is_valid_agent_name(new_name)
        if errors:
            gr.Warning(errors)
            return gr.update(value=None), gr.update(visible=False)
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                gr.Warning("You must be signed in to rename an agent.")
                return gr.update(value=None), gr.update(visible=False)
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if agent is None:
                gr.Warning("Agent not found.")
                return gr.update(value=None), gr.update(visible=False)
            if not check_user_permissions_write(user, agent):
                gr.Warning("You do not have permission to rename this agent.")
                return gr.update(value=None), gr.update(visible=False)
            agent.name = new_name
            session.add(agent)
            session.commit()
            agent_id = agent.id

        agents = self.load_agents(user_id)
        agents = [(agent.name, agent.id) for agent in agents]
        return gr.update(choices=agents, value=agent_id), gr.update(visible=False)

    def is_valid_agent_name(self, name):
        if not name or not name.strip():
            return "Agent name cannot be empty."
        if len(name) > 50:
            return "Agent name cannot exceed 50 characters."
        if any(char in name for char in r'\/:*?"<>|'):
            return 'Agent name cannot contain special characters: \\ / : * ? " < > |'
        return None

    def on_register_events(self):
        self.btn_agent_rn.click(
            fn=lambda: gr.update(visible=True),
            outputs=[self.agent_rn],
            show_progress="hidden",
        )
        self.btn_new.click(
            fn=lambda: gr.update(visible=True),
            outputs=[self.agent_new],
            show_progress="hidden",
        )
        self.agent_new.submit(
            fn=self.new_agent,
            inputs=[
                self._app.user_id,
                self.agent_new,
            ],
            outputs=[
                self.agent_dropdown,
                self.selected_agent,
                self.agent_rn,
            ],
            show_progress="hidden",
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=[self.agent_new],
            show_progress="hidden",
        )
        self.agent_dropdown.select(
            fn=self.select_agent,
            inputs=[
                self._app.user_id,
                self.agent_dropdown,
            ],
            outputs=[
                self.agent_dropdown,
                self.selected_agent,
                self.agent_rn,
            ],
            show_progress="hidden",
        )
        self.agent_rn.submit(
            fn=self.rename_agent,
            inputs=[
                self._app.user_id,
                self.selected_agent,
                self.agent_rn,
            ],
            outputs=[
                self.agent_dropdown,
                self.agent_rn,
            ],
            show_progress="hidden",
        )
        self.btn_del.click(
            fn=lambda: gr.update(visible=True),
            outputs=[self._delete_confirm],
            show_progress="hidden",
        )
        self.btn_del_cnl.click(
            fn=lambda: gr.update(visible=False),
            outputs=[self._delete_confirm],
            show_progress="hidden",
        )
        self.btn_del_conf.click(
            fn=self.delete_agent,
            inputs=[
                self._app.user_id,
                self.selected_agent,
            ],
            outputs=[
                self.agent_dropdown,
                self.selected_agent,
            ],
            show_progress="hidden",
        ).then(
            fn=lambda: gr.update(visible=False),
            outputs=[self._delete_confirm],
            show_progress="hidden",
        )

    def on_subscribe_public_events(self):
        self._app.subscribe_event(
            name="onSignIn",
            definition={
                "fn": self.refresh_agent_list,
                "inputs": [self._app.user_id],
                "outputs": [
                    self.agent_dropdown,
                ],
                "show_progress": "hidden",
            },
        )
        self._app.subscribe_event(
            name="onSignOut",
            definition={
                "fn": lambda: gr.update(choices=[], value=None),
                "outputs": [self.agent_dropdown],
                "show_progress": "hidden",
            },
        )
    