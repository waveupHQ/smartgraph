# Interactive Story Collaborator using SmartGraph

from smartgraph import ReactiveAssistantConversation, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components import HumanInTheLoopComponent, TextInputHandler


class StoryAgent(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Generate the next part of the story
        return f"Next part of the story based on: {input_data}"


async def main():
    graph = ReactiveSmartGraph()

    # Create components
    user_input = TextInputHandler("UserInput")
    story_generator = StoryAgent("StoryGenerator")
    human_feedback = HumanInTheLoopComponent("HumanFeedback")

    # Create nodes
    input_node = ReactiveNode("input", user_input)
    story_node = ReactiveNode("story", story_generator)
    feedback_node = ReactiveNode("feedback", human_feedback)

    # Add nodes to the graph
    for node in [input_node, story_node, feedback_node]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("input", "story"))
    graph.add_edge(ReactiveEdge("story", "feedback"))
    graph.add_edge(ReactiveEdge("feedback", "story"))

    # Run the story collaboration
    story_so_far = ""
    for _ in range(3):  # Generate 3 parts of the story
        user_prompt = await graph.execute("input", "Continue the story")
        story_part = await graph.execute("story", user_prompt)
        feedback = await graph.execute("feedback", story_part)
        story_so_far += story_part + "\n"
        print(f"Story part: {story_part}")
        print(f"Human feedback: {feedback}")

    print("\nFinal story:")
    print(story_so_far)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
