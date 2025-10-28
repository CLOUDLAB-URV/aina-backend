from copy import deepcopy
from typing import Any

from ktem.index.base import BaseIndex
from ktem.settings import BaseSettingGroup

from api.app import app


def populate_agent_settings(
    overrides: dict[str, Any], index: BaseIndex, reasoning: str
) -> dict[str, Any]:
    """Populate agent settings with default values where not overridden."""
    settings = deepcopy(app.default_settings)
    settings.index.options[index.id] = BaseSettingGroup(
        settings=index.get_user_settings()
    )
    settings.reasoning.options[reasoning] = BaseSettingGroup(
        settings=app.reasonings[reasoning].get_user_settings()
    )
    settings.reasoning.finalize()
    settings.index.finalize()
    settings_flat = deepcopy(settings.flatten())
    settings_flat.update(overrides)
    return settings_flat
