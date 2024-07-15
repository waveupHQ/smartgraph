from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import networkx as nx


class GraphVisualizer:
    @staticmethod
    def draw_graph(graph: nx.DiGraph, output_file: Optional[str] = None, **kwargs: Any) -> None:
        """Draw the graph using matplotlib and networkx.

        Args:
            graph (nx.DiGraph): The graph to visualize.
            output_file (Optional[str]): If provided, save the visualization to this file.
            **kwargs: Additional keyword arguments for customization.
        """
        pos = nx.spring_layout(graph)
        plt.figure(figsize=kwargs.get("figsize", (12, 8)))

        # Draw nodes
        nx.draw_networkx_nodes(
            graph,
            pos,
            node_color=kwargs.get("node_color", "lightblue"),
            node_size=kwargs.get("node_size", 3000),
        )

        # Draw edges
        nx.draw_networkx_edges(graph, pos, edge_color=kwargs.get("edge_color", "gray"), arrows=True)

        # Add labels
        node_labels = {
            node: f"{data['node'].actor.name}\n{data['node'].task.description}"
            for node, data in graph.nodes(data=True)
        }
        nx.draw_networkx_labels(
            graph, pos, labels=node_labels, font_size=kwargs.get("font_size", 8)
        )

        # Add edge labels (conditions)
        edge_labels = {}
        for u, v, data in graph.edges(data=True):
            if data["edge"].conditions:
                condition_name = data["edge"].conditions[0].__name__
                if condition_name == "<lambda>":
                    condition_name = "condition"
                edge_labels[(u, v)] = condition_name
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels=edge_labels, font_size=kwargs.get("edge_label_font_size", 6)
        )

        plt.title(kwargs.get("title", "SmartGraph Visualization"))
        plt.axis("off")

        if output_file:
            plt.savefig(output_file, format="png", dpi=300, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

    @staticmethod
    def generate_mermaid_diagram(graph: nx.DiGraph) -> str:
        """Generate a Mermaid diagram representation of the graph.

        Args:
            graph (nx.DiGraph): The graph to visualize.

        Returns:
            str: Mermaid diagram representation of the graph.
        """
        mermaid = ["graph TD;"]

        for node, data in graph.nodes(data=True):
            node_name = f"{data['node'].actor.name}_{node}"
            mermaid.append(f'    {node}["{node_name}"];')

        for u, v, data in graph.edges(data=True):
            if data["edge"].conditions:
                condition_name = data["edge"].conditions[0].__name__
                if condition_name == "<lambda>":
                    condition_name = "condition"
                mermaid.append(f"    {u} -->|{condition_name}| {v};")
            else:
                mermaid.append(f"    {u} --> {v};")

        return "\n".join(mermaid)
