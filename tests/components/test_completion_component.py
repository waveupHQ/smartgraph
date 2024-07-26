# tests/test_completion_component.py

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smartgraph.components import CompletionComponent
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit


@pytest.fixture
def mock_litellm():
    with patch("smartgraph.components.completion_component.litellm") as mock:
        mock.acompletion = AsyncMock()
        yield mock


@pytest.fixture
def mock_duckduckgo_toolkit():
    toolkit = MagicMock(spec=DuckDuckGoToolkit)
    toolkit.functions = {
        "duckduckgo_search": AsyncMock(
            return_value='{"results": [{"title": "Test", "body": "This is a test result"}]}'
        )
    }
    toolkit.schemas = [
        {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "Search the web using DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    return toolkit


@pytest.mark.asyncio
async def test_conversation_flow(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    # Mock LLM responses
    mock_litellm.acompletion.side_effect = [
        MagicMock(choices=[MagicMock(message={"content": "Hello! How can I help you today?"})]),
        MagicMock(choices=[MagicMock(message={"content": "The weather in New York is sunny today."})]),
    ]

    # Test initial conversation
    response = await assistant.process({"message": "Hi there!"})
    assert response["ai_response"] == "Hello! How can I help you today?"
    assert len(assistant.conversation_history) == 2

    # Test follow-up question
    response = await assistant.process({"message": "What's the weather like in New York?"})
    assert response["ai_response"] == "The weather in New York is sunny today."
    assert len(assistant.conversation_history) == 4

    # Verify API calls
    assert mock_litellm.acompletion.call_count == 2
    assert mock_litellm.acompletion.call_args_list[0][1]["messages"][-1]["content"] == "Hi there!"
    assert mock_litellm.acompletion.call_args_list[1][1]["messages"][-1]["content"] == "What's the weather like in New York?"


@pytest.mark.asyncio
async def test_toolkit_integration(mock_litellm, mock_duckduckgo_toolkit):
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        toolkits=[mock_duckduckgo_toolkit],
    )

    # Mock LLM responses to simulate tool usage
    mock_litellm.acompletion.side_effect = [
        MagicMock(choices=[MagicMock(message={
            "content": None,
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "duckduckgo_search",
                    "arguments": '{"query": "Python programming"}'
                }
            }]
        })]),
        MagicMock(choices=[MagicMock(message={
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability."
        })]),
    ]

    response = await assistant.process({"message": "What is Python?"})

    assert "Python is a high-level, interpreted programming language" in response["ai_response"]
    mock_duckduckgo_toolkit.functions["duckduckgo_search"].assert_called_once_with(query="Python programming")


@pytest.mark.asyncio
async def test_error_handling(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    # Simulate an API error
    mock_litellm.acompletion.side_effect = Exception("API Error")

    response = await assistant.process({"message": "This should cause an error"})
    assert "error" in response
    assert "API Error" in response["error"]


@pytest.mark.asyncio
async def test_conversation_reset(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    mock_litellm.acompletion.return_value = MagicMock(
        choices=[MagicMock(message={"content": "Hello!"})]
    )

    await assistant.process({"message": "Hi"})
    assert len(assistant.conversation_history) == 2

    assistant.clear_conversation_history()
    assert len(assistant.conversation_history) == 0

    await assistant.process({"message": "Hello again"})
    assert len(assistant.conversation_history) == 2
