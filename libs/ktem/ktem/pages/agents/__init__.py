import gradio as gr
from ktem.app import BasePage


class AgentsTab(BasePage):
    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Agents")
                gr.Markdown(
                    "This is a placeholder for the Agents management page. "
                    "You can add, edit, and manage your agents here."
                )