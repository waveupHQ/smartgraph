import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smartgraph import AIActor, HumanActor, MemoryManager, Node, SmartGraph, Task
from smartgraph.assistant_conversation import AssistantConversation
from smartgraph.core import Edge


@pytest.fixture
def memory_manager():
    return MemoryManager()


@pytest.fixture
def assistant():
    return AsyncMock(spec=AssistantConversation)


@pytest.fixture
def human_actor(memory_manager):
    return HumanActor("User", memory_manager=memory_manager)


@pytest.fixture
def ai_actor(memory_manager, assistant):
    return AIActor("AI", assistant=assistant, memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_human_actor_perform_task(human_actor):
    task = Task(description="Test task")
    with patch("builtins.input", return_value="test query"):
        result = await human_actor.perform_task(task, {}, {})
    assert result == {"response": "test query"}


@pytest.mark.asyncio
async def test_ai_actor_perform_task(ai_actor):
    task = Task(description="Test task")
    ai_actor.assistant.run.return_value = "AI response"
    result = await ai_actor.perform_task(task, {"input": "test query"}, {})
    assert result == {"response": "AI response"}


@pytest.mark.asyncio
async def test_assistant_conversation():
    assistant = AssistantConversation(name="Test Assistant", model="test-model", api_key="test-key")

    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message={"content": "Test response"})]
        )

        response = await assistant.run("Test prompt")

    assert response == "Test response"
    assert len(assistant.messages) == 2  # User message and assistant response  # noqa: PLR2004


@pytest.mark.asyncio
async def test_assistant_conversation_with_tool_calls():
    assistant = AssistantConversation(name="Test Assistant", model="test-model", api_key="test-key")
    assistant.add_function("test_function", lambda x: f"Function result: {x}")

    with patch("litellm.completion") as mock_completion:
        mock_completion.side_effect = [
            MagicMock(
                choices=[
                    MagicMock(
                        message={
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call1",
                                    "function": {
                                        "name": "test_function",
                                        "arguments": '{"x": "test"}',
                                    },
                                }
                            ],
                        }
                    )
                ]
            ),
            MagicMock(choices=[MagicMock(message={"content": "Final response"})]),
        ]

        response = await assistant.run("Test prompt")

    assert response == "Final response"
    assert (
        len(assistant.messages) == 4  # noqa: PLR2004
    )  # User message, assistant tool call, function response, final response


if __name__ == "__main__":
    pytest.main()
