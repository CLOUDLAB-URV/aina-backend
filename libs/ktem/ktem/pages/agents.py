
from ktem.app import BasePage


class AgentsTab(BasePage):
    def __init__(self, app):
        self._app = app
        self.on_building_ui()
