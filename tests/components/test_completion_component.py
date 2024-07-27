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
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"],
                },
            },
        }
    ]
    return toolkit

@pytest.mark.asyncio
async def test_initialization():
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        system_context="You are a helpful assistant.",
        max_tokens=1000,
        stream=False
    )
    assert assistant.name == "TestAssistant"
    assert assistant.model == "gpt-3.5-turbo"
    assert assistant.system_context == "You are a helpful assistant."
    assert assistant.max_tokens == 1000
    assert assistant.stream == False
    assert len(assistant.conversation_history) == 1
    assert assistant.conversation_history[0] == {"role": "system", "content": "You are a helpful assistant."}

@pytest.mark.asyncio
async def test_conversation_flow(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    mock_litellm.acompletion.side_effect = [
        MagicMock(choices=[MagicMock(message={"content": "Hello! How can I help you today?"})]),
        MagicMock(choices=[MagicMock(message={"content": "The weather in New York is sunny today."})]),
    ]

    response1 = await assistant.process({"message": "Hi there!"})
    print(f"Expected: 'Hello! How can I help you today?'")
    print(f"Actual: '{response1['ai_response']}'")
    assert response1["ai_response"] == "Hello! How can I help you today?"
    assert len(assistant.conversation_history) == 3

    response2 = await assistant.process({"message": "What's the weather like in New York?"})
    print(f"Expected: 'The weather in New York is sunny today.'")
    print(f"Actual: '{response2['ai_response']}'")
    assert response2["ai_response"] == "The weather in New York is sunny today."
    assert len(assistant.conversation_history) == 5

    assert mock_litellm.acompletion.call_count == 2
    assert mock_litellm.acompletion.call_args_list[0][1]["messages"][-1]["content"] == "Hi there!"
    assert mock_litellm.acompletion.call_args_list[1][1]["messages"][-1]["content"] == "What's the weather like in New York?"

@pytest.mark.asyncio
async def test_clear_conversation_history():
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        system_context="You are a helpful assistant.",
        api_key="test_key"
    )

    # Add some conversation history
    assistant.conversation_history.extend([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
    ])

    assert len(assistant.conversation_history) == 5  # Including system message

    # Clear conversation history
    assistant.clear_conversation_history()

    # Check if only system message remains
    assert len(assistant.conversation_history) == 1
    assert assistant.conversation_history[0] == {"role": "system", "content": "You are a helpful assistant."}

@pytest.mark.asyncio
async def test_set_system_context():
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        system_context="You are a helpful assistant.",
        api_key="test_key"
    )

    # Change system context
    new_context = "You are a professional writer."
    assistant.set_system_context(new_context)

    assert assistant.system_context == new_context
    assert assistant.conversation_history[0] == {"role": "system", "content": new_context}

@pytest.mark.asyncio
async def test_set_max_tokens():
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    initial_max_tokens = assistant.max_tokens
    new_max_tokens = 2000

    assistant.set_max_tokens(new_max_tokens)

    assert assistant.max_tokens == new_max_tokens
    assert assistant.max_tokens != initial_max_tokens

@pytest.mark.asyncio
async def test_add_toolkit():
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")
    mock_toolkit = MagicMock(spec=DuckDuckGoToolkit)

    initial_toolkit_count = len(assistant.toolkits)
    assistant.add_toolkit(mock_toolkit)

    assert len(assistant.toolkits) == initial_toolkit_count + 1
    assert mock_toolkit in assistant.toolkits

@pytest.mark.asyncio
async def test_error_handling(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key")

    mock_litellm.acompletion.side_effect = Exception("API Error")

    response = await assistant.process({"message": "This should cause an error"})
    assert "error" in response
    assert "API Error" in response["error"]

@pytest.mark.asyncio
async def test_streaming_mode(mock_litellm):
    assistant = CompletionComponent(name="TestAssistant", model="gpt-3.5-turbo", api_key="test_key", stream=True)

    mock_litellm.acompletion.return_value = AsyncMock()
    mock_litellm.acompletion.return_value.__aiter__.return_value = [
        {"choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": " world"}}]},
        {"choices": [{"delta": {"content": "!"}}]},
    ]

    response_generator = await assistant.process({"message": "Hi"})
    
    full_response = ""
    async for chunk in response_generator:
        if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
            full_response += chunk["choices"][0]["delta"]["content"]

    assert full_response == "Hello world!"

@pytest.mark.asyncio
async def test_toolkit_integration(mock_litellm, mock_duckduckgo_toolkit):
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        toolkits=[mock_duckduckgo_toolkit],
    )

    mock_litellm.acompletion.side_effect = [
        MagicMock(
            choices=[
                MagicMock(
                    message={
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "duckduckgo_search",
                                    "arguments": '{"query": "Python programming"}',
                                },
                            }
                        ],
                    }
                )
            ]
        ),
        MagicMock(
            choices=[
                MagicMock(
                    message={
                        "content": "Python is a high-level, interpreted programming language known for its simplicity and readability."
                    }
                )
            ]
        ),
    ]

    response = await assistant.process({"message": "What is Python?"})

    assert "Python is a high-level, interpreted programming language" in response["ai_response"]
    mock_duckduckgo_toolkit.functions["duckduckgo_search"].assert_called_once_with(query="Python programming")

@pytest.mark.asyncio
async def test_prepare_messages():
    assistant = CompletionComponent(
        name="TestAssistant",
        model="gpt-3.5-turbo",
        system_context="You are a helpful assistant.",
        api_key="test_key"
    )

    # Add some conversation history
    assistant.conversation_history.extend([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ])

    messages = assistant._prepare_messages("How are you?")

    assert len(messages) == 4
    assert messages[0] == {"role": "system", "content": "You are a helpful assistant."}
    assert messages[1] == {"role": "user", "content": "Hello"}
    assert messages[2] == {"role": "assistant", "content": "Hi there!"}
    assert messages[3] == {"role": "user", "content": "How are you?"}
