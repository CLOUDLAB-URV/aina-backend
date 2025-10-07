from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from kotaemon.base import Document
from .base import BaseReasoning
from typing import Optional
import logging
import asyncio


logger = logging.getLogger(__name__)


class MCPPipeline(BaseReasoning):
    """The reasoning pipeline that handles each of the user chat messages

    This reasoning pipeline has access to:
        - the retrievers
        - the user settings
        - the message
        - the conversation id
        - the message history
    """

    @classmethod
    def get_info(cls) -> dict:
        """Get the pipeline information for the app to organize and display"""
        return {
            "id": "mcp",
            "name": "MCP Pipeline",
            "description": "MCP Pipeline",
        }

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
            },
        }

    @classmethod
    def get_pipeline(
        cls,
        user_settings: dict,
        state: dict,
        retrievers: Optional[list] = None,
    ):
        """Get the reasoning pipeline for the app to execute

        Args:
            user_setting: user settings
            state: conversation state
            retrievers (list): List of retrievers
        """

        cls.tools = []
        cls.tools = connect()
        print(cls.tools)
        return cls()

    def run(self, message: str, conv_id: str, history: list, **kwargs):  # type: ignore
        """Execute the reasoning pipeline"""
        logging.warning("MCP Reasoning Pipeline is not 2 implemented yet.")
        raise NotImplementedError
    
    def stream(  # type: ignore
        self, message: str, conv_id: str, history: list, **kwargs  # type: ignore
    ):
        """Stream the reasoning pipeline output"""
        logging.warning("MCP Reasoning Pipeline streaming is not implemented yet.")

        response = self.process_message(message=message)
        messages=""
        for msg in response:
            if isinstance(msg, AIMessage):
                content = msg.content or ""  # proteger contra None
                if "</think>" in content:
                    final = content.index("</think>") + len("</think>")
                    msg_text = content[final:]  # todo después de </think>
                else:
                    msg_text = content
                messages += msg_text

        # result = [Document(channnel="chat",content=response) for response in response]
        result = [Document(channel="chat",content=messages)]
        logging.warning(f"The value of the response of the mcp is == {response} and the result is {result}")
        return result

    def process_message(
        self,
        message: str,
    ) -> tuple:
        return asyncio.run(self._procces_query(message))

    async def _procces_query(self, message):
        logging.info("Processing query")
        agent = create_react_agent(
            model=init_chat_model(model="qwen3:8b",model_provider="ollama",base_url="http://192.168.1.105:11434"),
            tools=self.tools,
        )
        response = await agent.ainvoke({"messages": message})
        logging.info("Done Processing Query")
        response = response.get("messages")
        logging.info("The response from the agent is %s", response)
        return response

def connect():

    async def _connect():
        client = MultiServerMCPClient({
            "duckduckgo": {
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            }
        })
        print(f"Hello {client}")
        tools = await client.get_tools()
        print(f"Tools {tools}")
        return tools 

    return asyncio.run(_connect())