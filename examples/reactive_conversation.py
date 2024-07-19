# examples/reactive_conversation.py

import asyncio
import os

from dotenv import load_dotenv

from smartgraph.assistant_conversation import ReactiveAssistantConversation

load_dotenv()


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY is not set in the environment variables.")

    assistant = ReactiveAssistantConversation(name="Example Assistant", api_key=api_key)

    # Initial context
    initial_context = {
        "user_info": "This is a test user.",
        "assistant_role": "You are an AI assistant that is aware of its context and can reference it in conversation.",
        "conversation_goal": "Demonstrate the assistant's ability to use context in its responses.",
    }
    assistant.update_context(initial_context)

    async def ask_question(question):
        print(f"\nUser: {question}")
        response = await assistant.process(question)
        print(f"Assistant: {response}")

    # First question
    await ask_question(
        "Hello, can you tell me about the context you have and how you're using it in this conversation?"
    )

    # Update context
    new_context = {
        "user_preference": "The user prefers concise responses.",
        "conversation_topic": "We are discussing AI and machine learning.",
    }
    assistant.update_context(new_context)

    # Second question to demonstrate updated context
    await ask_question(
        "Can you tell me how the context has changed and how it affects your responses?"
    )


if __name__ == "__main__":
    asyncio.run(main())
