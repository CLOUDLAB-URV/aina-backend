from api.app import app


class ReasoningService:
    def __init__(self):
        pass

    def list_reasonings(self):
        return list(app.default_settings.reasoning.options.keys())
