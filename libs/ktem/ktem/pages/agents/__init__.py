import gradio as gr
from ktem.app import BasePage

from .users import AgentUsers

class AgentsTab(BasePage):
    def __init__(self, app):
        self._app = app
        self.selected_agent = gr.State(None)
        self.on_building_ui()

    def on_building_ui(self):
        with gr.Row():
            with gr.Column():
                self.agent_dropdown = gr.Dropdown(
                    label="Select Agent",
                    choices=[],
                    interactive=True,
                )
                self.agent_users = AgentUsers(self)
