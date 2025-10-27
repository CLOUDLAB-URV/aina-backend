from api.app import app


class ReasoningService:
    def __init__(self):
        pass

    def list_reasonings(self):
        return list(app.default_settings.reasoning.options.keys())

    def get_reasoning_config(self, reasoning_name: str):
        if reasoning_name not in app.default_settings.reasoning.options:
            raise LookupError(f"Reasoning '{reasoning_name}' not found")
        return app.default_settings.reasoning.options[reasoning_name].settings
