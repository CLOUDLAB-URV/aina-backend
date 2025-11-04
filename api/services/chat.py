from copy import deepcopy
from typing import Any

from ktem.db.engine import engine
from ktem.db.models import Agent, Conversation, User
from ktem.index.base import BaseIndex
from ktem.index.file.index import FileIndex
from ktem.pages.agents.common import has_access
from ktem.pages.chat.chat_suggestion import ChatSuggestion
from ktem.pages.chat.common import STATE
from ktem.utils.conversation import sync_retrieval_n_message
from sqlmodel import Session, select
from theflow.settings import settings as flowsettings

from api.app import app
from api.core.utils import populate_agent_settings
from api.schemas.chat import ChatRequest, ConversationInfo, SelectMode
from kotaemon.base.schema import Document

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

    def select_conversation(
        self,
        agent_id: str,
        conversation_id: str,
        user_id: str,
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
                    f"to access agent {agent_id}"
                )

            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                raise LookupError(f"Conversation with id {conversation_id} not found")
            if conversation.user != user_id:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access conversation {conversation_id}"
                )
            if conversation.agent_id != agent_id:
                raise PermissionError(
                    f"Conversation with id {conversation_id} is not associated "
                    f"with agent {agent_id}"
                )

            return self._select_conversation(conversation)

    def _select_conversation(
        self,
        conversation: Conversation,
    ):
        default_chat_suggestions = [[s] for s in ChatSuggestion.CHAT_SAMPLES]

        selected = conversation.data_source.get("selected", {})
        messages = conversation.data_source.get("messages", [])

        chat_suggestions = conversation.data_source.get(
            "chat_suggestions", default_chat_suggestions
        )

        retrieval_messages: list[str] = conversation.data_source.get(
            "retrieval_messages", []
        )
        plot_history: list[dict] = conversation.data_source.get("plot_history", [])

        retrieval_messages = sync_retrieval_n_message(messages, retrieval_messages)
        state = conversation.data_source.get("state", STATE)

        return ConversationInfo(
            messages=messages,
            chat_suggestions=chat_suggestions,
            retrieval_messages=retrieval_messages,
            plot_history=plot_history,
            selected=selected,
            state=state,
            likes=conversation.data_source.get("likes", []),
        )

    def like_message(
        self,
        agent_id: str,
        conversation_id: str,
        user_id: str,
        message_index: int,
        liked: bool | str = True,
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
                    f"to access agent {agent_id}"
                )

            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                raise LookupError(f"Conversation with id {conversation_id} not found")
            if conversation.user != user_id:
                raise PermissionError(
                    f"User with id {user_id} does not have permission "
                    f"to access conversation {conversation_id}"
                )
            if conversation.agent_id != agent_id:
                raise PermissionError(
                    f"Conversation with id {conversation_id} is not associated "
                    f"with agent {agent_id}"
                )

            data_source = deepcopy(conversation.data_source)

            idx = [message_index, 1]  # second dimension is 1 (agent message)
            _, message = data_source.get("messages", [])[message_index]

            likes = data_source.get("likes", [])
            likes.append([idx, message, liked])

            data_source["likes"] = likes
            conversation.data_source = data_source

            session.add(conversation)
            session.commit()

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

            result = self._select_conversation(conversation)
            chat_history: list[tuple[str, str]] = result.messages
            chat_state: dict[str, Any] = result.state

            # if input is empty, assume regen mode
            if not request.message:
                chat_state["app"]["regen"] = True

            pipeline, reasoning_state = self._create_pipeline(
                agent=agent,
                user_id=user_id,
                settings=settings,
                state=app.chat_state,
                request=request,
            )

            text, refs, plot = "", "", None
            try:
                for response in pipeline.stream(
                    request.message, conversation_id, chat_history
                ):
                    print(response)
                    if not isinstance(response, Document):
                        continue
                    if response.channel is None:
                        continue
                    if response.channel == "chat":
                        if response.content is None:
                            text = ""
                        else:
                            text += response.content
                    if response.channel == "info":
                        if response.content is None:
                            refs = ""
                        else:
                            refs += response.content
                    if response.channel == "plot":
                        plot = response.content

                    chat_state[pipeline.get_info()["id"]] = reasoning_state["pipeline"]

                    yield response.model_dump_json()
            except Exception as e:
                raise e

            if not text:
                text = getattr(
                    flowsettings,
                    "KH_CHAT_EMPTY_MSG_PLACEHOLDER",
                    "(Sorry, I don't know)",
                )

            chat_history = chat_history + [(request.message, text)]

            self._persist_data_source(
                session=session,
                conversation=conversation,
                user=user,
                agent=agent,
                retrieval_msg=refs,
                messages=chat_history,
                retrieval_history=result.retrieval_messages,
                plot_data=plot,
                plot_history=result.plot_history,
                state=chat_state,
                select_mode=request.select_mode,
                selected_files=request.selected_files,
            )

    def _persist_data_source(
        self,
        session: Session,
        conversation: Conversation,
        user: User,
        agent: Agent,
        retrieval_msg: str,
        plot_data,
        retrieval_history: list[str],
        plot_history,
        messages: list[tuple[str, str]],
        state: dict[str, Any],
        select_mode: SelectMode,
        selected_files: list[str],
    ):
        # if not regen, then append the new message
        if not state["app"].get("regen", False):
            retrieval_history = retrieval_history + [retrieval_msg]
            plot_history = plot_history + [plot_data]
        else:
            if retrieval_history:
                retrieval_history[-1] = retrieval_msg
                plot_history[-1] = plot_data

        # reset regen state
        state["app"]["regen"] = False

        data_source = conversation.data_source

        selected = {
            str(agent.index_id): [select_mode.value, selected_files, user.id],
        }

        conversation.data_source = {
            "selected": selected,
            "messages": messages,
            "retrieval_messages": retrieval_history,
            "plot_history": plot_history,
            "state": state,
            "likes": deepcopy(data_source.get("likes", [])),
        }
        session.add(conversation)
        session.commit()

        return retrieval_history, plot_history

    def _create_pipeline(
        self,
        agent: Agent,
        user_id: str,
        settings: dict,
        state: dict,
        request: ChatRequest,
    ):
        reasoning_type = request.reasoning_type
        llm_type = request.llm_type
        use_mind_map = request.use_mind_map
        use_citation = request.use_citation
        language = request.language
        select_mode = request.select_mode
        selected_files = request.selected_files

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
