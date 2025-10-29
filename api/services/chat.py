from copy import deepcopy

from ktem.db.engine import engine
from ktem.db.models import Agent, Conversation, User
from ktem.index.base import BaseIndex
from ktem.index.file.index import FileIndex
from ktem.pages.agents.common import has_access
from sqlmodel import Session, select

from api.app import app
from api.core.utils import populate_agent_settings
from api.schemas.chat import ChatRequest, SelectMode

DEFAULT_SETTING = "(default)"


class ChatService:
    def __init__(self):
        pass

    def _get_index(self, agent: Agent) -> BaseIndex:
        index_id = agent.index_id
        if index_id is None:
            raise LookupError(f"Agent with id {agent.id} has no index assigned")
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        return index

    def chat_with_agent(
        self,
        agent_id: str,
        conversation_id: str,
        user_id: str,
        request: ChatRequest,
    ):
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user is None:
                raise LookupError(f"User with id {user_id} not found")

            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")

            if not has_access(user, agent):
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to chat with agent {agent_id}"
                )

            index = self._get_index(agent)

            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                raise LookupError(f"Conversation with id {conversation_id} not found")
            if conversation.user != user_id:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access conversation {conversation_id}"
                )

            settings = populate_agent_settings(
                agent.settings or {}, index, agent.reasoning_id
            )

            pipeline, reasoning_state = self._create_pipeline(
                agent=agent,
                user_id=user_id,
                settings=settings,
                state=app.chat_state,
                reasoning_type=request.reasoning_type,
                llm_type=request.llm_type,
                use_mind_map=request.use_mind_map,
                use_citation=request.use_citation,
                language=request.language,
                select_mode=request.select_mode,
                selected_files=request.selected_files,
            )

            history = [(request.message, "")]

            try:
                for response in pipeline.stream(
                    request.message, conversation_id, history
                ):
                    print(response)
                    yield response.model_dump_json()
            except Exception as e:
                raise e

    def _create_pipeline(
        self,
        agent: Agent,
        user_id: str,
        settings: dict,
        state: dict,
        reasoning_type: str | None = None,
        llm_type: str | None = None,
        use_mind_map: bool | None = None,
        use_citation: bool | None = None,
        language: str | None = None,
        select_mode: SelectMode = SelectMode.ALL,
        selected_files: list[str] = [],
    ):
        reasoning_mode = (
            settings["reasoning.use"]
            if reasoning_type in (DEFAULT_SETTING, None)
            else reasoning_type
        )
        reasoning_cls = app.reasonings[reasoning_mode]
        reasoning_id = reasoning_cls.get_info()["id"]

        settings = deepcopy(settings)
        llm_setting_key = f"reasoning.options.{reasoning_id}.llm"
        if llm_setting_key in settings and llm_type not in (
            DEFAULT_SETTING,
            None,
            "",
        ):
            settings[llm_setting_key] = llm_type

        if use_mind_map not in (DEFAULT_SETTING, None):
            settings["reasoning.options.simple.create_mindmap"] = use_mind_map

        if use_citation not in (DEFAULT_SETTING, None):
            settings["reasoning.options.simple.highlight_citation"] = use_citation

        if language not in (DEFAULT_SETTING, None):
            settings["reasoning.lang"] = language

        # get retrievers
        retrievers = []

        index_selected = [select_mode.value, selected_files, user_id]

        indices = self._get_indices_for_agent(agent)

        for index in indices:
            if not isinstance(index, FileIndex):
                raise TypeError(f"Index with id {index.id} is not a FileIndex")
            index._selector_ui = _Wrapper(index)
            iretreivers = index.get_retriever_pipelines(
                settings,
                user_id,  # type: ignore
                index_selected,
            )
            retrievers.extend(iretreivers)

        reasoning_state = {
            "app": deepcopy(state["app"]),
            "pipeline": deepcopy(state.get(reasoning_id, {})),
        }

        pipeline = reasoning_cls.get_pipeline(settings, reasoning_state, retrievers)

        return pipeline, reasoning_state

    def _get_indices_for_agent(self, agent: Agent) -> list[BaseIndex]:
        if not agent.index:
            return []
        return [i for i in app.index_manager.indices if i.id == agent.index_id]


class _Wrapper:
    def __init__(self, index: FileIndex) -> None:
        self._index = index

    def get_selected_ids(self, selected):
        mode, selected, user_id = selected[0], selected[1], selected[2]
        if user_id is None:
            return []
        if mode == "disabled":
            return []
        if mode == "select":
            return selected

        file_ids = []
        with Session(engine) as session:
            statement = select(self._index._resources["Source"].id)  # type: ignore
            if self._index.config.get("private", False):
                statement = statement.where(
                    self._index._resources["Source"].user == user_id  # type: ignore
                )
            results = session.execute(statement).all()
            for (id,) in results:
                file_ids.append(id)

        return file_ids
