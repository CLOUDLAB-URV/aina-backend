import gradio as gr
from ktem.app import BasePage

class AgentUsers(BasePage):
    def __init__(self, app):
        self._app = app
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
