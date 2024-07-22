# Automated Customer Support Ticket Classifier and Router using SmartGraph

from smartgraph import ReactiveAssistantConversation, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components import BranchingComponent, TextInputHandler


class TicketClassifier(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Simplified classification logic
        if "payment" in input_data.lower():
            return "billing"
        elif "login" in input_data.lower():
            return "technical"
        else:
            return "general"


class TicketPrioritizer(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Simplified prioritization logic
        urgent_keywords = ["urgent", "immediately", "critical"]
        if any(keyword in input_data.lower() for keyword in urgent_keywords):
            return "high"
        return "normal"


class TicketRouter(ReactiveAssistantConversation):
    async def process(self, input_data):
        category, priority = input_data
        if category == "billing":
            return f"Routed to Billing Department with {priority} priority"
        elif category == "technical":
            return f"Routed to Technical Support with {priority} priority"
        else:
            return f"Routed to General Customer Service with {priority} priority"


async def main():
    graph = ReactiveSmartGraph()

    # Create components
    ticket_input = TextInputHandler("TicketInput")
    classifier = TicketClassifier("TicketClassifier")
    prioritizer = TicketPrioritizer("TicketPrioritizer")
    router = TicketRouter("TicketRouter")

    # Create nodes
    input_node = ReactiveNode("input", ticket_input)
    classify_node = ReactiveNode("classify", classifier)
    prioritize_node = ReactiveNode("prioritize", prioritizer)
    route_node = ReactiveNode("route", router)

    # Add nodes to the graph
    for node in [input_node, classify_node, prioritize_node, route_node]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("input", "classify"))
    graph.add_edge(ReactiveEdge("input", "prioritize"))
    graph.add_edge(ReactiveEdge("classify", "route"))
    graph.add_edge(ReactiveEdge("prioritize", "route"))

    # Process a ticket
    ticket = "I can't log into my account and need help immediately!"
    category = await graph.execute("classify", ticket)
    priority = await graph.execute("prioritize", ticket)
    routing = await graph.execute("route", (category, priority))

    print(f"Ticket: {ticket}")
    print(f"Classification: {category}")
    print(f"Priority: {priority}")
    print(f"Routing: {routing}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
