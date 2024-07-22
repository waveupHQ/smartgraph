# examples/human_in_the_loop_smartgraph_example.py

import asyncio

from smartgraph import ReactiveAssistantConversation, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components.human_in_the_loop import (
    BasicApprovalComponent,
    CorrectionRefinementComponent,
    GuidedDecisionMakingComponent,
    IterativeFeedbackComponent,
)
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit


async def main():
    graph = ReactiveSmartGraph()

    # Create components
    approval = BasicApprovalComponent("ApprovalComponent")
    correction = CorrectionRefinementComponent("CorrectionComponent")
    decision_making = GuidedDecisionMakingComponent("DecisionMakingComponent")
    iterative_feedback = IterativeFeedbackComponent("IterativeFeedbackComponent")

    duckduckgo_toolkit = DuckDuckGoToolkit(max_results=3)
    assistant = ReactiveAssistantConversation(
        name="Interactive Assistant",
        toolkits=[duckduckgo_toolkit],
        model="gpt-4-0613",
        api_key="your-api-key-here",
    )

    # Create nodes
    approval_node = ReactiveNode("approval", approval)
    correction_node = ReactiveNode("correction", correction)
    decision_node = ReactiveNode("decision", decision_making)
    feedback_node = ReactiveNode("feedback", iterative_feedback)
    assistant_node = ReactiveNode("assistant", assistant)

    # Add nodes to the graph
    for node in [approval_node, correction_node, decision_node, feedback_node, assistant_node]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("assistant", "approval"))
    graph.add_edge(ReactiveEdge("assistant", "correction"))
    graph.add_edge(ReactiveEdge("assistant", "decision"))
    graph.add_edge(ReactiveEdge("assistant", "feedback"))

    # Simulated workflow
    initial_input = "What's the best approach to learn machine learning?"

    # Assistant generates initial response
    assistant_output = await graph.execute("assistant", initial_input)

    # Approval workflow
    approval_result = await graph.execute("approval", assistant_output)
    approval.submit_human_input(True)  # Simulate human approval
    print("Approval result:", await approval_result)

    # Correction workflow
    correction_result = await graph.execute("correction", assistant_output)
    correction.submit_human_input(
        "Add more emphasis on practical projects"
    )  # Simulate human correction
    print("Correction result:", await correction_result)

    # Decision making workflow
    decision_result = await graph.execute("decision", assistant_output)
    decision_making.submit_human_input("Option A")  # Simulate human decision
    print("Decision result:", await decision_result)

    # Iterative feedback workflow
    feedback_result = await graph.execute("feedback", assistant_output)
    iterative_feedback.submit_human_input(
        {"feedback": "Provide more details on online courses", "complete": False}
    )
    iterative_feedback.submit_human_input(
        {"feedback": "Include book recommendations", "complete": True}
    )
    print("Feedback result:", await feedback_result)


if __name__ == "__main__":
    asyncio.run(main())
