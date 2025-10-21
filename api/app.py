from ktem.index.manager import IndexManager
from ktem.reasoning.base import BaseReasoning
from ktem.settings import BaseSettingGroup, SettingGroup, SettingReasoningGroup
from theflow.settings import settings
from theflow.utils.modules import import_dotted_string

DEFAULT_APPLICATION_STATE = {"regen": False}
STATE = {
    "app": DEFAULT_APPLICATION_STATE,
}


class App:
    def __init__(self):
        self.reasonings: dict[str, type[BaseReasoning]] = {}
        self.chat_state = STATE
        self.default_settings = SettingGroup(
            application=BaseSettingGroup(settings=settings.SETTINGS_APP),
            reasoning=SettingReasoningGroup(settings=settings.SETTINGS_REASONING),
        )
        self._register_reasonings()
        self.initialize_indices()

    def initialize_indices(self):
        """Create the index manager, start indices, and register to app settings"""
        self.index_manager = IndexManager(self)
        self.index_manager.on_application_startup()

        # index: BaseIndex
        # for index in self.index_manager.indices:
        #     options = index.get_user_settings()
        #     self.default_settings.index.options[index.id] = BaseSettingGroup(
        #         settings=options
        #     )

    def _register_reasonings(self):
        """Register the reasoning components from app settings"""
        if getattr(settings, "KH_REASONINGS", None) is None:
            return

        for value in settings.KH_REASONINGS:
            reasoning_cls: type[BaseReasoning] = import_dotted_string(value, safe=False)
            rid: str = reasoning_cls.get_info()["id"]
            self.reasonings[rid] = reasoning_cls
            options = reasoning_cls().get_user_settings()
            self.default_settings.reasoning.options[rid] = BaseSettingGroup(
                settings=options
            )


app = App()
