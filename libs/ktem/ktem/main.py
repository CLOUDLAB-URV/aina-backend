import gradio as gr
from decouple import config
from ktem.app import BaseApp
from ktem.db.base_models import Role
from ktem.pages.chat import ChatPage
from ktem.pages.help import HelpPage
from ktem.pages.agents import AgentsTab
from ktem.pages.resources import ResourcesTab
from ktem.pages.settings import SettingsPage
from ktem.pages.setup import SetupPage
from theflow.settings import settings as flowsettings
from ktem.db.engine import engine
from ktem.db.models import User, Agent
from sqlmodel import Session, select, or_

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

# override first setup setting
if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False


def toggle_first_setup_visibility():
    global KH_APP_DATA_EXISTS
    is_first_setup = not KH_DEMO_MODE and not KH_APP_DATA_EXISTS
    KH_APP_DATA_EXISTS = True
    return gr.update(visible=is_first_setup), gr.update(visible=not is_first_setup)


class App(BaseApp):
    """The main app of Kotaemon

    The main application contains app-level information:
        - setting state
        - user id

    App life-cycle:
        - Render
        - Declare public events
        - Subscribe public events
        - Register events
    """

    def get_user_accessible_indices(self, user_id):
        """Get indices that a user has access to based on their role and agent permissions"""
        if not user_id:
            return []

        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                return []

            # Admin can see all indices
            if user.role == Role.ADMIN:
                return self.index_manager.indices

            # Chat users cannot see any indices
            if user.role == Role.CHAT_USER:
                return []

            # Agent creators can see indices from agents they have access to
            if user.role == Role.AGENT_CREATOR:
                # Get agents the user can access (created by them or they have access to)
                agents = session.exec(
                    select(Agent).where(
                        or_(
                            Agent.creators.contains(user),
                            Agent.users.contains(user),
                        )
                    ).distinct()
                ).all()

                # Get unique index IDs from these agents
                accessible_index_ids = set()
                for agent in agents:
                    if agent.index_id:
                        accessible_index_ids.add(agent.index_id)

                # Return indices that match these IDs
                return [idx for idx in self.index_manager.indices if idx.id in accessible_index_ids]

            return []

    def declare_index_events(self):
        """Declare events for all indices to ensure they're available for subscription"""
        for index in self.index_manager.indices:
            # Declare the FileIndex changed event for each index
            event_name = f"onFileIndex{index.id}Changed"
            if event_name not in self._events:
                self.declare_event(event_name)

    def ui(self):
        """Render the UI"""
        self._tabs = {}

        with gr.Tabs() as self.tabs:
            if self.f_user_management:
                from ktem.pages.login import LoginPage

                with gr.Tab(
                    "Welcome", elem_id="login-tab", id="login-tab"
                ) as self._tabs["login-tab"]:
                    self.login_page = LoginPage(self)

            with gr.Tab(
                "Chat",
                elem_id="chat-tab",
                id="chat-tab",
                visible=not self.f_user_management,
            ) as self._tabs["chat-tab"]:
                self.chat_page = ChatPage(self)

            with gr.Tab(
                "Agents",
                elem_id="agents-tab",
                id="agents-tab",
                elem_classes=["fill-main-area-height", "scrollable"],
                visible=not self.f_user_management,
            ) as self._tabs["agents-tab"]:
                self.agents_page = AgentsTab(self)

            # Dynamic index rendering with security - only render authorized indices
            @gr.render(inputs=[self.user_id], triggers=[self.user_id.change])
            def render_user_indices(user_id):
                # Don't show indices tab for demo mode
                if KH_DEMO_MODE:
                    return
                
                # Don't show indices if user management is enabled but no user is logged in
                if self.f_user_management and not user_id:
                    return
                
                accessible_indices = self.get_user_accessible_indices(user_id)
                
                # Don't show if user has no access to any indices
                if not accessible_indices:
                    return

                # Render index tabs dynamically based on user access
                # Render single index as direct tab
                if len(accessible_indices) == 1:
                    index = accessible_indices[0]
                    with gr.Tab(
                        f"{index.name}",
                        elem_id="indices-tab",
                        elem_classes=[
                            "fill-main-area-height",
                            "scrollable", 
                            "indices-tab",
                        ],
                        id="indices-tab",
                    ):
                        page = index.get_index_page_ui()
                        
                # Render multiple indices under Files tab
                elif len(accessible_indices) > 1:
                    with gr.Tab(
                        "Files",
                        elem_id="indices-tab",
                        elem_classes=["fill-main-area-height", "scrollable", "indices-tab"],
                        id="indices-tab",
                    ):
                        for index in accessible_indices:
                            with gr.Tab(
                                index.name,
                                elem_id=f"{index.id}-tab",
                            ):
                                page = index.get_index_page_ui()

            if not KH_DEMO_MODE:
                if not KH_SSO_ENABLED:
                    with gr.Tab(
                        "Resources",
                        elem_id="resources-tab",
                        id="resources-tab",
                        visible=not self.f_user_management,
                        elem_classes=["fill-main-area-height", "scrollable"],
                    ) as self._tabs["resources-tab"]:
                        self.resources_page = ResourcesTab(self)

                with gr.Tab(
                    "Settings",
                    elem_id="settings-tab",
                    id="settings-tab",
                    visible=not self.f_user_management,
                    elem_classes=["fill-main-area-height", "scrollable"],
                ) as self._tabs["settings-tab"]:
                    self.settings_page = SettingsPage(self)

            with gr.Tab(
                "Help",
                elem_id="help-tab",
                id="help-tab",
                visible=not self.f_user_management,
                elem_classes=["fill-main-area-height", "scrollable"],
            ) as self._tabs["help-tab"]:
                self.help_page = HelpPage(self)

        if KH_ENABLE_FIRST_SETUP:
            with gr.Column(visible=False) as self.setup_page_wrapper:
                self.setup_page = SetupPage(self)

    def declare_public_events(self):
        """Declare an event for the app including index events"""
        # Call parent implementation first
        super().declare_public_events()
        # Declare all index events
        self.declare_index_events()

    def on_subscribe_public_events(self):
        if self.f_user_management:

            def toggle_login_visibility(user_id):
                if not user_id:
                    return list(
                        (
                            gr.update(visible=True)
                            if k == "login-tab"
                            else gr.update(visible=False)
                        )
                        for k in self._tabs.keys()
                    ) + [gr.update(selected="login-tab")]

                with Session(engine) as session:
                    user = session.exec(select(User).where(User.id == user_id)).first()
                    if user is None:
                        return list(
                            (
                                gr.update(visible=True)
                                if k == "login-tab"
                                else gr.update(visible=False)
                            )
                            for k in self._tabs.keys()
                        )

                    is_admin = user.role == Role.ADMIN
                    is_agent_creator = user.role == Role.AGENT_CREATOR

                tabs_update = []
                for k in self._tabs.keys():
                    if k == "login-tab":
                        tabs_update.append(gr.update(visible=False))
                    elif k == "agents-tab":
                        tabs_update.append(gr.update(visible=is_agent_creator or is_admin))
                    elif k == "resources-tab":
                        tabs_update.append(gr.update(visible=is_admin))
                    else:
                        tabs_update.append(gr.update(visible=True))

                tabs_update.append(gr.update(selected="chat-tab"))

                return tabs_update

            self.subscribe_event(
                name="onSignIn",
                definition={
                    "fn": toggle_login_visibility,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()) + [self.tabs],
                    "show_progress": "hidden",
                },
            )

            self.subscribe_event(
                name="onSignOut",
                definition={
                    "fn": toggle_login_visibility,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()) + [self.tabs],
                    "show_progress": "hidden",
                },
            )

        if KH_ENABLE_FIRST_SETUP:
            self.subscribe_event(
                name="onFirstSetupComplete",
                definition={
                    "fn": toggle_first_setup_visibility,
                    "inputs": [],
                    "outputs": [self.setup_page_wrapper, self.tabs],
                    "show_progress": "hidden",
                },
            )

    def _on_app_created(self):
        """Called when the app is created"""

        if KH_ENABLE_FIRST_SETUP:
            self.app.load(
                toggle_first_setup_visibility,
                inputs=[],
                outputs=[self.setup_page_wrapper, self.tabs],
            )
