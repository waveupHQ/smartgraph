# examples/advanced_branching_assistant.py

import asyncio
import os

from dotenv import load_dotenv

from smartgraph import ReactiveSmartGraph
from smartgraph.components import BranchingComponent, CompletionComponent, TextInputHandler
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit

load_dotenv()


def is_question(data: dict) -> bool:
    content = data.get("content", "")
    return "?" in content or any(
        word in content.lower() for word in ["what", "why", "how", "when", "where", "who"]
    )


def is_greeting(data: dict) -> bool:
    content = data.get("content", "").lower()
    return any(word in content for word in ["hello", "hi", "hey", "greetings"])


def is_command(data: dict) -> bool:
    content = data.get("content", "").lower()
    return content.startswith(("please", "could you", "would you", "can you"))


class AdvancedBranchingAssistant(ReactiveSmartGraph):
    def __init__(self):
        super().__init__()
        pipeline = self.create_pipeline("AdvancedBranchingAssistant")

        pipeline.add_component(TextInputHandler("TextInput"))

        branching = BranchingComponent("InputRouter")
        pipeline.add_component(branching)

        question_handler = CompletionComponent(
            "QuestionHandler",
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            toolkits=[DuckDuckGoToolkit()],
            system_context="You are a helpful assistant that answers questions.",
        )

        greeting_handler = CompletionComponent(
            "GreetingHandler",
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            system_context="You are a friendly assistant that responds to greetings.",
        )

        command_handler = CompletionComponent(
            "CommandHandler",
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            system_context="You are a helpful assistant that follows commands and instructions.",
        )

        default_handler = CompletionComponent(
            "DefaultHandler",
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            system_context="You are a general-purpose assistant that can handle various types of input.",
        )

        branching.add_branch(is_greeting, greeting_handler, "greeting")
        branching.add_branch(is_question, question_handler, "question")
        branching.add_branch(is_command, command_handler, "command")
        branching.set_default_branch(default_handler)

        self.compile()

    async def process(self, query):
        return await self.execute("AdvancedBranchingAssistant", query)


async def main():
    assistant = AdvancedBranchingAssistant()

    inputs = [
        "What's the capital of France?",
        "Hello, how are you today?",
        "Please summarize the latest news on AI.",
        "I like pizza.",
    ]

    for input_text in inputs:
        result = await assistant.process(input_text)
        print(f"\nInput: {input_text}")
        print(f"Branch taken: {result.get('branch')}")
        print(f"Result: {result.get('result', {}).get('ai_response', 'No response')}")


if __name__ == "__main__":
    asyncio.run(main())

