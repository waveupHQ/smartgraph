# Dynamic Sales Proposal Generator using SmartGraph

from smartgraph import ReactiveAssistantConversation, ReactiveEdge, ReactiveNode, ReactiveSmartGraph
from smartgraph.components import AggregatorComponent, StructuredDataInputHandler


class ClientAnalyzer(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Simplified client analysis
        return {
            "size": "large" if input_data["annual_revenue"] > 1000000 else "small",
            "industry": input_data["industry"],
            "pain_points": input_data["pain_points"]
        }

class ProductMatcher(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Simplified product matching logic
        if input_data["industry"] == "technology" and "efficiency" in input_data["pain_points"]:
            return ["CRM Software", "Project Management Tool"]
        return ["Generic Solution A", "Generic Solution B"]

class PricingStrategy(ReactiveAssistantConversation):
    async def process(self, input_data):
        # Simplified pricing strategy
        client_size, products = input_data
        base_price = 1000 if client_size == "large" else 500
        return {product: base_price * (i + 1) for i, product in enumerate(products)}

class ProposalGenerator(ReactiveAssistantConversation):
    async def process(self, input_data):
        client_info, products, pricing = input_data
        proposal = f"Proposal for {client_info['industry']} client\n\n"
        proposal += f"Recommended Solutions:\n"
        for product in products:
            proposal += f"- {product}: ${pricing[product]}\n"
        proposal += f"\nTotal Value: ${sum(pricing.values())}"
        return proposal

async def main():
    graph = ReactiveSmartGraph()

    # Create components
    client_input = StructuredDataInputHandler("ClientInput")
    client_analyzer = ClientAnalyzer("ClientAnalyzer")
    product_matcher = ProductMatcher("ProductMatcher")
    pricing_strategy = PricingStrategy("PricingStrategy")
    proposal_generator = ProposalGenerator("ProposalGenerator")
    aggregator = AggregatorComponent("DataAggregator")

    # Create nodes
    input_node = ReactiveNode("input", client_input)
    analyze_node = ReactiveNode("analyze", client_analyzer)
    match_node = ReactiveNode("match", product_matcher)
    price_node = ReactiveNode("price", pricing_strategy)
    generate_node = ReactiveNode("generate", proposal_generator)
    aggregate_node = ReactiveNode("aggregate", aggregator)

    # Add nodes to the graph
    for node in [input_node, analyze_node, match_node, price_node, generate_node, aggregate_node]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("input", "analyze"))
    graph.add_edge(ReactiveEdge("analyze", "match"))
    graph.add_edge(ReactiveEdge("analyze", "price"))
    graph.add_edge(ReactiveEdge("match", "price"))
    graph.add_edge(ReactiveEdge("analyze", "aggregate"))
    graph.add_edge(ReactiveEdge("match", "aggregate"))
    graph.add_edge(ReactiveEdge("price", "aggregate"))
    graph.add_edge(ReactiveEdge("aggregate", "generate"))

    # Generate a proposal
    client_data = {
        "annual_revenue": 2000000,
        "industry": "technology",
        "pain_points": ["efficiency", "scalability"]
    }
    
    client_analysis = await graph.execute("analyze", client_data)
    matched_products = await graph.execute("match", client_analysis)
    pricing = await graph.execute("price", (client_analysis["size"], matched_products))
    aggregated_data = await graph.execute("aggregate", [client_analysis, matched_products, pricing])
    proposal = await graph.execute("generate", aggregated_data)

    print(proposal)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
