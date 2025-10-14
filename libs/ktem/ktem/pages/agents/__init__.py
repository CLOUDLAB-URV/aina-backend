import gradio as gr
from ktem.app import BasePage

from .control import AgentControl
from .dropdown import AgentSettings
from .users import AgentUsers


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
