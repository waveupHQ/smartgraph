# tests/test_reactive_assistant_conversation.py

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smartgraph import ReactiveAssistantConversation
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit


@pytest.fixture
def mock_litellm():
    with patch("smartgraph.assistant_conversation.litellm") as mock:
        mock.acompletion = AsyncMock()
        yield mock


@pytest.fixture
def mock_duckduckgo_toolkit():
    toolkit = MagicMock(spec=DuckDuckGoToolkit)
    toolkit.search = AsyncMock(
        return_value='{"results": [{"title": "Test", "body": "This is a test result"}]}'
    )
    return toolkit


@pytest.mark.asyncio
async def test_conversation_flow_and_context(mock_litellm):
    assistant = ReactiveAssistantConversation(name="TestAssistant", api_key="test_key")

    # Mock LLM responses
    mock_litellm.acompletion.side_effect = [
        MagicMock(choices=[MagicMock(message={"content": "Hello! How can I help you today?"})]),
        MagicMock(
            choices=[MagicMock(message={"content": "The weather in New York is sunny today."})]
        ),
    ]

    # Test initial conversation
    response = await assistant.process("Hi there!")
    assert response == "Hello! How can I help you today?"
    assert len(assistant.messages.value) == 2

    # Update context and test context-aware response
    assistant.update_context({"location": "New York"})
    response = await assistant.process("What's the weather like?")
    assert response == "The weather in New York is sunny today."
    assert len(assistant.messages.value) == 4

    # Verify context was used in the API call
    context_call = mock_litellm.acompletion.call_args_list[1][1]
    assert any(
        "location" in msg["content"] for msg in context_call["messages"] if msg["role"] == "system"
    )


@pytest.mark.asyncio
async def test_toolkit_integration_no_function_call(mock_litellm, mock_duckduckgo_toolkit):
    assistant = ReactiveAssistantConversation(
        name="TestAssistant",
        toolkits=[mock_duckduckgo_toolkit],
        model="gpt-4o-mini",
    )

    mock_litellm.acompletion.return_value = MagicMock(
        choices=[
            MagicMock(
                message={
                    "content": "Python is a high-level, interpreted programming language known for its simplicity and readability."
                }
            )
        ]
    )

    response = await assistant.process("What is Python?")

    assert "Python is a high-level, interpreted programming language" in response
    mock_duckduckgo_toolkit.functions["duckduckgo_search"].assert_not_called()


@pytest.mark.asyncio
async def test_error_handling_and_recovery(mock_litellm):
    assistant = ReactiveAssistantConversation(name="TestAssistant", api_key="test_key")

    # Simulate an API error
    mock_litellm.acompletion.side_effect = Exception("API Error")

    response = await assistant.process("This should cause an error")
    assert "an error occurred" in response.lower()

    # Simulate recovery
    mock_litellm.acompletion.side_effect = None
    mock_litellm.acompletion.return_value = MagicMock(
        choices=[MagicMock(message={"content": "I've recovered!"})]
    )

    response = await assistant.process("Are you working now?")
    assert response == "I've recovered!"


@pytest.mark.asyncio
async def test_conversation_reset(mock_litellm):
    assistant = ReactiveAssistantConversation(name="TestAssistant", api_key="test_key")

    mock_litellm.acompletion.return_value = MagicMock(
        choices=[MagicMock(message={"content": "Hello!"})]
    )

    await assistant.process("Hi")
    assert len(assistant.messages.value) == 2

    assistant.reset_conversation()
    assert len(assistant.messages.value) == 0

    await assistant.process("Hello again")
    assert len(assistant.messages.value) == 2
