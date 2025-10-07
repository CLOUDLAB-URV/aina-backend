import logging
import threading
from textwrap import dedent
from typing import Generator, Optional
# from mcp.client.streamable_http import streamablehttp_client
# from mcp.client.session import ClientSession
from decouple import config
from ktem.embeddings.manager import embedding_models_manager as embeddings
from ktem.llms.manager import llms
from ktem.reasoning.prompt_optimization import (
    DecomposeQuestionPipeline,
    RewriteQuestionPipeline,
)
import asyncio
from ktem.utils.render import Render
from ktem.utils.visualize_cited import CreateCitationVizPipeline
from plotly.io import to_json

from kotaemon.base import (
    AIMessage,
    BaseComponent,
    Document,
    HumanMessage,
    Node,
    RetrievedDocument,
    SystemMessage,
)
from kotaemon.indices.qa.citation_qa import (
    CONTEXT_RELEVANT_WARNING_SCORE,
    DEFAULT_QA_TEXT_PROMPT,
    AnswerWithContextPipeline,
)
from kotaemon.indices.qa.citation_qa_inline import AnswerWithInlineCitation
from kotaemon.indices.qa.format_context import PrepareEvidencePipeline
from kotaemon.indices.qa.utils import replace_think_tag_with_details
from kotaemon.llms import ChatLLM

from ..utils import SUPPORTED_LANGUAGE_MAP
from .base import BaseReasoning

logger = logging.getLogger(__name__)

class MCPPipeline(BaseReasoning):
    """Question answering pipeline. Handle from question to answer"""

    """The reasoning pipeline that handles each of the user chat messages

    This reasoning pipeline has access to:
        - the retrievers
        - the user settings
        - the message
        - the conversation id
        - the message history
    """

    @classmethod
    def get_user_settings(cls) -> dict:
        """Get the default user settings for this pipeline"""
        from ktem.llms.manager import llms

        llm = ""
        choices = [("(default)", "")]
        try:
            choices += [(_, _) for _ in llms.options().keys()]
        except Exception as e:
            logger.exception(f"Failed to get LLM options: {e}")

        return {
            "llm": {
                "name": "Language model",
                "value": llm,
                "component": "dropdown",
                "choices": choices,
                "special_type": "llm",
                "info": (
                    "The language model to use for generating the answer. If None, "
                    "the application default language model will be used."
                ),
            }}

    @classmethod
    def get_pipeline(
        cls,
        user_settings: dict,
        state: dict,
        retrievers: Optional[list["BaseComponent"]] = None,
    ) -> "BaseReasoning":
        """Get the reasoning pipeline for the app to execute

        Args:
            user_setting: user settings
            state: conversation state
            retrievers (list): List of retrievers
        """

        cls.tools = [{"name": "MCP Tool", "description": "MCP Tool", "parameters": {}}]
        # cls.connect()

        return cls()
    
    # def connect(self,) -> str:
    #     return asyncio.run(self._connect())

    # async def _connect(self) -> None:
    #     try:
    #         # for server in servers:
    #             async with streamablehttp_client(
    #                 url="https://127.0.0.1:8000/mcp",
    #                 headers={},
    #             ) as (read_stream, write_stream, _):
    #                 async with ClientSession(
    #                     read_stream, write_stream
    #                 ) as local_session:
    #                     await local_session.initialize()
    #                     tools = await local_session.list_tools()
    #                     for tool in tools.tools:
    #                         self.tools.append(
    #                             {
    #                                 "name": tool.name,
    #                                 "description": tool.description,
    #                                 "parameters": tool.inputSchema,
    #                             }
    #                         )
    #                         self.tool_url[tool.name] = {
    #                             "url": "https://127.0.0.1:8000/mcp",
    #                             "headers": {},
    #                         }
    #     except Exception as e:
    #         print(f"An error happened so connect hasn't finished executing {e}")
    #     return "tools_registered"

    def run(self, message: str, conv_id: str, history: list, **kwargs):  # type: ignore
        """Execute the reasoning pipeline"""
        raise NotImplementedError

    def stream( 
        self, message: str, conv_id: str, history: list, **kwargs  # type: ignore
    ):
        """Stream the reasoning pipeline"""
        print(f"THis is the result of {self.tools}")
        return [Document(
            content="MCP Pipeline is currently disabled.",
            channel="chat"
        )]
    
    @classmethod
    def get_info(cls) -> dict:
        """Get the pipeline information for the app to organize and display"""
        return {
            "id": "mcp",
            "name": "MCP Pipeline",
            "description": "MCP Pipeline",
        }