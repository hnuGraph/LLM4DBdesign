from typing import List
from typing_extensions import Self
from pydantic import BaseModel

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage
from autogen_core import Component

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

class RoleChatCompletionContextConfig(BaseModel):
    names: List[str]
    initial_messages: List[LLMMessage] | None = None


class RoleChatCompletionContext(ChatCompletionContext, Component[RoleChatCompletionContextConfig]):
    """A chat completion context that keeps a view of the specific assistant,
    Args:
        name (int): The name of the assistant.
        initial_messages (List[LLMMessage] | None): The initial messages.
    """

    component_config_schema = RoleChatCompletionContextConfig
    # component_provider_override = "autogen_core.model_context.HeadAndTailChatCompletionContext"

    def __init__(self, name: str, initial_messages: List[LLMMessage] | None = None) -> None:
        super().__init__(initial_messages)
        self._name = name

    async def get_messages(self) -> List[LLMMessage]:
        """Get messages from the specific assistant"""
        # Filter out thought field from AssistantMessage.
        messages_out: List[LLMMessage] = []
        for message in self._messages:
            if message.source in self._name:
                messages_out.append(message)
        return messages_out

    def _to_config(self) -> RoleChatCompletionContextConfig:
        return RoleChatCompletionContextConfig(
            name=self._name, initial_messages=self._initial_messages
        )

    @classmethod
    def _from_config(cls, config: RoleChatCompletionContextConfig) -> Self:
        return cls(name=config.name, initial_messages=config.initial_messages)


class RecipientChatCompletionContext(ChatCompletionContext, Component[RoleChatCompletionContextConfig]):
    """A chat completion context that keeps a view of the specific assistant,
    Args:
        name (int): The name of the assistant.
        initial_messages (List[LLMMessage] | None): The initial messages.
    """

    component_config_schema = RoleChatCompletionContextConfig
    # component_provider_override = "autogen_core.model_context.HeadAndTailChatCompletionContext"

    def __init__(self, name: str, initial_messages: List[LLMMessage] | None = None) -> None:
        super().__init__(initial_messages)
        self._name = name

    async def get_messages(self) -> List[LLMMessage]:
        """Get messages from the specific assistant"""
        # Filter out thought field from AssistantMessage.
        messages_out: List[LLMMessage] = []
        for message in self._messages:
            for each_name in self._name:
                if each_name in message.content or message.source == each_name:
                    messages_out.append(message)
        return messages_out

    def _to_config(self) -> RoleChatCompletionContextConfig:
        return RoleChatCompletionContextConfig(
            name=self._name, initial_messages=self._initial_messages
        )

    @classmethod
    def _from_config(cls, config: RoleChatCompletionContextConfig) -> Self:
        return cls(name=config.name, initial_messages=config.initial_messages)
