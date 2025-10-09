import asyncio
import logging
from typing import Optional

from ktem.llms.manager import llms
from ktem.reasoning.base import BaseReasoning
from ktem.utils.render import Render
from langchain.schema.messages import AIMessage as LCAIMessage
from langchain.schema.messages import AIMessageChunk, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from kotaemon.base import (
    AIMessage,
    BaseComponent,
    Document,
    HumanMessage,
    Node,
    SystemMessage,
)
from kotaemon.indices.qa.utils import replace_think_tag_with_details
from kotaemon.llms import ChatLLM

logger = logging.getLogger(__name__)

DEFAULT_MCP_SERVERS = {
    "duckduckgo": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable_http",
    }
}


class MCPPipeline(BaseReasoning):
    """MCP-based reasoning pipeline using ReactAgent with MCP tools."""

    class Config:
        allow_extra = True

    retrievers: list[BaseComponent]
    llm: ChatLLM = Node(default_callback=lambda _: llms.get_default())
    mcp_client: Optional[MultiServerMCPClient] = None
    mcp_servers: dict = DEFAULT_MCP_SERVERS
    system_prompt: str = ""

    _states: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mcp_tools = []
        self._states = {}

    async def _initialize_mcp_client(self):
        """Initialize the MCP client with configured servers"""
        if not self.mcp_client:
            try:
                self.mcp_client = MultiServerMCPClient(self.mcp_servers)
                # Get tools from MCP servers
                self._mcp_tools = await self.mcp_client.get_tools()

                logger.info(
                    "Initialized MCP client with %d tools", len(self._mcp_tools)
                )
            except (ConnectionError, RuntimeError, ValueError) as e:
                logger.error("Failed to initialize MCP client: %s", e)
                self._mcp_tools = []

    def display_tool(self, call_id, name, output) -> Document:
        header = "<b>Tool call id {call_id} result</b>".format(call_id=call_id)
        content = (
            "<b>Tool call</b>: <em>{name}</em>\n\n<b>Output</b>: {output}"
        ).format(
            name=name,
            output=output,
        )
        return Document(
            channel="info",
            content=Render.collapsible(
                header=header,
                content=Render.table(content),
                open=True,
            ),
        )

    def display_tool_call(self, call_id, name, arguments) -> Document:
        header = "<b>Tool call id {call_id} invocation</b>".format(call_id=call_id)
        content = "<b>Tool call</b>: <em>{name}({arguments})</em>".format(
            name=name,
            arguments=arguments,
        )
        return Document(
            channel="info",
            content=Render.collapsible(
                header=header,
                content=Render.table(content),
                open=True,
            ),
        )

    def process_stream(self, stream_mode, chunk):
        if stream_mode == "messages":
            (msg, _) = chunk
            if isinstance(msg, AIMessageChunk):
                if len(msg.content) > 0:
                    return msg.content, Document(content=msg.content, channel="chat")
        elif stream_mode == "updates":
            if "tools" in chunk:
                tools = chunk["tools"]["messages"]
                tool_docs = []
                for tool_msg in tools:
                    if isinstance(tool_msg, ToolMessage):
                        tool_docs.append(
                            Document(
                                channel="info",
                                content=self.display_tool(
                                    tool_msg.tool_call_id,
                                    tool_msg.name,
                                    tool_msg.content,
                                ),
                            )
                        )
                return tool_docs
            if "agent" in chunk:
                messages = chunk["agent"]["messages"]
                tool_docs = []
                for msg in messages:
                    if isinstance(msg, LCAIMessage):
                        calls = msg.additional_kwargs.get("tool_calls", [])
                        for call in calls:
                            call_id = call.get("id", "unknown")
                            function = call.get("function", {})
                            name = function.get("name", "unknown")
                            arguments = function.get("arguments", "")
                            tool_docs.append(
                                Document(
                                    channel="info",
                                    content=self.display_tool_call(
                                        call_id, name, arguments
                                    ),
                                )
                            )
                return tool_docs
        return None

    def stream(
        self, message: str, conv_id: str, history: list, **kwargs
    ):  # type: ignore
        # Initialize MCP client synchronously
        asyncio.run(self._initialize_mcp_client())

        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        for human, ai in history:
            messages.append(HumanMessage(content=human))
            messages.append(AIMessage(content=ai))

        messages.append(HumanMessage(content=message))

        agent = create_react_agent(
            model=self.llm.to_langchain_format(), tools=self._mcp_tools
        )

        async def consume(*args, **kwargs):
            async for stream_mode, chunk in agent.astream(*args, **kwargs):
                yield stream_mode, chunk

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agen = consume({"messages": messages}, stream_mode=["updates", "messages"])

        output = ""
        try:
            while True:
                try:
                    stream_mode, chunk = loop.run_until_complete(agen.__anext__())
                    result = self.process_stream(stream_mode, chunk)
                    if result:
                        if isinstance(result, list):
                            yield from result
                        if isinstance(result, tuple):
                            text, doc = result
                            output += text
                            yield doc
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

        # except NotImplementedError:
        #     output = agent.invoke({"messages": messages})["messages"]
        #     response = output[-1].content

        processed_answer = replace_think_tag_with_details(output)
        if processed_answer != output:
            # clear the chat message and render again
            yield Document(channel="chat", content=None)
            yield Document(channel="chat", content=processed_answer)

        # if logprobs:
        #     qa_score = np.exp(np.average(logprobs))
        # else:
        #     qa_score = None

        answer = Document(text=output)  # , metadata={"qa_score": qa_score})

        return answer

    @classmethod
    def get_info(cls) -> dict:
        return {
            "id": "mcp",
            "name": "MCP Agent",
            "description": (
                "A reasoning pipeline that uses Model Context Protocol (MCP) tools "
                "with a ReactAgent. MCP allows integration with external tools and "
                "services through a standardized protocol. Configure MCP servers "
                "in the settings to add custom tools and capabilities."
            ),
        }

    @classmethod
    def get_pipeline(
        cls, settings: dict, states: dict, retrievers: list | None = None
    ) -> BaseReasoning:
        _id = cls.get_info()["id"]
        prefix = f"reasoning.options.{_id}"

        llm_name = settings[f"{prefix}.llm"]
        llm = llms.get(llm_name, llms.get_default())

        settings.get("reasoning.max_context_length", None)

        # Parse MCP servers configuration
        mcp_servers_setting = settings.get(f"{prefix}.mcp_servers", "")
        mcp_servers = DEFAULT_MCP_SERVERS
        if mcp_servers_setting.strip():
            try:
                import json

                mcp_servers = json.loads(mcp_servers_setting)
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Failed to parse MCP servers config: %s, using default", e
                )

        pipeline = cls(retrievers=retrievers)
        pipeline.mcp_servers = mcp_servers
        pipeline.llm = llm
        pipeline.system_prompt = settings[f"{prefix}.system_prompt"]

        # Store states for potential future use
        pipeline._states = states

        return pipeline

    @classmethod
    def get_user_settings(cls) -> dict:
        llm = ""
        llm_choices = [("(default)", "")]
        try:
            llm_choices += [(_, _) for _ in llms.options().keys()]
        except (AttributeError, ImportError, KeyError) as e:
            logger.exception("Failed to get LLM options: %s", e)

        import json

        default_mcp_config = json.dumps(DEFAULT_MCP_SERVERS, indent=2)

        return {
            "llm": {
                "name": "Language model",
                "value": llm,
                "component": "dropdown",
                "choices": llm_choices,
                "special_type": "llm",
                "info": (
                    "The language model to use for generating the answer. If None, "
                    "the application default language model will be used."
                ),
            },
            "mcp_servers": {
                "name": "MCP Servers Configuration",
                "value": default_mcp_config,
                "component": "text",
                "kwargs": {"lines": 10},
                "info": (
                    "JSON configuration for MCP servers. Each server should have "
                    "a name, URL, and transport type. Example format shown above."
                ),
            },
            "system_prompt": {
                "name": "System Prompt",
                "value": ("This is a question answering system."),
            },
        }
