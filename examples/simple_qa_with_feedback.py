import asyncio
import os
from typing import Any, Dict

from dotenv import load_dotenv

from smartgraph import ReactiveAssistantConversation, ReactiveNode, ReactiveSmartGraph
from smartgraph.components import HumanInTheLoopComponent
from smartgraph.logging import SmartGraphLogger

# Load environment variables (for API key)
load_dotenv()

logger = SmartGraphLogger.get_logger()
logger.set_level("ERROR")


class LLMQAAgent(ReactiveAssistantConversation):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Use an appropriate model
        )

    async def process(self, input_data: str) -> str:
        prompt = f"Please answer the following question concisely: {input_data}"
        response = await super().process(prompt)
        return response


class FeedbackComponent(HumanInTheLoopComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.feedback_options = ["Good", "Needs improvement", "Bad"]
        self.current_option = 0

    async def _generate_system_output(self, input_data: Any) -> Dict[str, Any]:
        return {"prompt": f"Please rate the answer: {input_data}"}

    async def _get_human_input(self, system_output: Any, timeout: float = 60.0) -> Any:
        # Simulate human input
        await asyncio.sleep(1)  # Simulate a short delay
        feedback = self.feedback_options[self.current_option]
        self.current_option = (self.current_option + 1) % len(self.feedback_options)
        return feedback

    async def _process_human_input(self, human_input: Any, system_output: Any) -> Any:
        return f"Feedback received: {human_input}"


async def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    graph = ReactiveSmartGraph()

    # Create components
    qa_agent = LLMQAAgent("QAAgent")
    feedback = FeedbackComponent("FeedbackComponent")

    # Create nodes
    qa_node = ReactiveNode("qa", qa_agent)
    feedback_node = ReactiveNode("feedback", feedback)

    # Add nodes to the graph
    graph.add_node(qa_node)
    graph.add_node(feedback_node)

    # Note: We're not adding any edges here

    # Run the QA system with feedback
    questions = [
        "What is the capital of France?",
        "Who wrote Romeo and Juliet?",
        "What is the boiling point of water?",
    ]

    for question in questions:
        print(f"\nQuestion: {question}")

        try:
            # Get answer from QA agent
            answer = await graph.execute("qa", question)
            print(f"Answer: {answer}")

            # Get feedback on the answer
            feedback = await graph.execute("feedback", answer)
            print(f"Feedback: {feedback}")
        except Exception as e:
            logger.error(f"Error processing question '{question}': {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
