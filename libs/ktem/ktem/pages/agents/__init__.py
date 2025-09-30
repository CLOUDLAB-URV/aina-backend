import gradio as gr
from ktem.app import BasePage
from ktem.db.engine import engine
from ktem.db.models import Agent, User
from ktem.db.base_models import Role
from sqlmodel import Session, select

from .users import AgentUsers
from .control import AgentControl
from .dropdown import AgentSettings

class AgentsTab(BasePage):
    def __init__(self, app):
        self._app = app
        self.selected_agent = gr.State(None)
        self.on_building_ui()

    def on_building_ui(self):
        with gr.Row():
            with gr.Column(scale=1):
                self.agent_control = AgentControl(self._app, self.selected_agent)
                self.agent_users = AgentUsers(self._app, self.selected_agent)
                self.agent_settings = AgentSettings(self._app, self.selected_agent)
            # with gr.Column(scale=3):
