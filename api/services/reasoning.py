from api.app import app


class ReasoningService:
    def __init__(self):
        pass

    def list_reasonings(self):
        return list(app.reasonings.keys())

    def get_reasoning_config(self, reasoning_name: str):
        if reasoning_name not in app.reasonings:
            raise LookupError(f"Reasoning '{reasoning_name}' not found")
        return app.reasonings[reasoning_name].get_user_settings()

    def get_reasoning_app_settings(self):
        return {
            k: app.default_settings.reasoning.settings[k].model_dump(exclude_unset=True)
            for k in app.default_settings.reasoning.settings
        }
