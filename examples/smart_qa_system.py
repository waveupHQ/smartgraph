# examples/smart_qa_system.py

import asyncio
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table

from smartgraph import (
    ReactiveAIComponent,
    ReactiveAssistantConversation,
    ReactiveEdge,
    ReactiveNode,
    ReactiveSmartGraph,
)
from smartgraph.logging import SmartGraphLogger
from smartgraph.tools.duckduckgo_toolkit import DuckDuckGoToolkit

load_dotenv()
logger = SmartGraphLogger.get_logger()
console = Console()


class QuestionAnalysisComponent(ReactiveAIComponent):
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        return {
            "question": question,
            "requires_search": any(
                word in question.lower() for word in ["who", "what", "when", "where", "why", "how"]
            ),
        }


class WebSearchComponent(ReactiveAIComponent):
    def __init__(self, name: str, toolkit: DuckDuckGoToolkit):
        super().__init__(name)
        self.toolkit = toolkit

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        try:
            search_results = await self.toolkit.search(question)
            return {
                "question": question,
                "search_results": json.loads(search_results),
                "search_successful": True,
            }
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"question": question, "search_results": [], "search_successful": False}


class AnswerFormulationComponent(ReactiveAssistantConversation):
    def __init__(self, name: str, api_key: str):
        super().__init__(name, api_key=api_key)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        search_results = input_data.get("search_results", [])
        search_successful = input_data.get("search_successful", False)

        if search_successful and search_results:
            search_results_str = "\n".join(
                [f"- {result['title']}: {result['body']}" for result in search_results[:3]]
            )
        else:
            search_results_str = "No search results available."

        prompt = f"""Question: {question}

        Search Results:
        {search_results_str}

        Please provide a concise and accurate answer to the question based on the search results provided. If the search results don't contain relevant information, use your general knowledge to answer the question."""

        response = await super().process(prompt)
        return {"question": question, "answer": response, "search_performed": search_successful}


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    graph = ReactiveSmartGraph()

    # Create components
    question_analysis = QuestionAnalysisComponent("QuestionAnalysis")
    duckduckgo_toolkit = DuckDuckGoToolkit(max_results=3)
    web_search = WebSearchComponent("WebSearch", duckduckgo_toolkit)
    answer_formulation = AnswerFormulationComponent("AnswerFormulation", api_key)

    # Create nodes
    analysis_node = ReactiveNode("analysis", question_analysis)
    search_node = ReactiveNode("search", web_search)
    answer_node = ReactiveNode("answer", answer_formulation)

    # Add nodes to the graph
    for node in [analysis_node, search_node, answer_node]:
        graph.add_node(node)

    # Add edges
    graph.add_edge(ReactiveEdge("analysis", "search", lambda data: data["requires_search"]))
    graph.add_edge(ReactiveEdge("analysis", "answer", lambda data: not data["requires_search"]))
    graph.add_edge(ReactiveEdge("search", "answer"))

    # Function to process a question through the graph
    async def process_question(question: str) -> str:
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Processing...", total=None)
                result = await graph.execute("analysis", {"question": question})
                progress.update(task, completed=100)
            return result["answer"]
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return f"[bold red]Sorry, I encountered an error while processing your question: {str(e)}[/bold red]"

    # Function to print state information using Rich
    def print_state_info(global_state, analysis_state, search_state, answer_state):
        table = Table(title="State Information", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="dim", width=20)
        table.add_column("State")

        table.add_row(
            "Global",
            Syntax(json.dumps(global_state, indent=2), "json", theme="monokai", line_numbers=True),
        )
        table.add_row(
            "Analysis Node",
            Syntax(
                json.dumps(analysis_state, indent=2), "json", theme="monokai", line_numbers=True
            ),
        )
        table.add_row(
            "Search Node",
            Syntax(json.dumps(search_state, indent=2), "json", theme="monokai", line_numbers=True),
        )
        table.add_row(
            "Answer Node",
            Syntax(json.dumps(answer_state, indent=2), "json", theme="monokai", line_numbers=True),
        )

        console.print(table)

    # Example usage
    questions = [
        "What is the capital of France?",
        "How are you doing today?",
        "Who won the Nobel Prize in Physics in 2022?",
    ]

    show_state = Confirm.ask("Do you want to display detailed state information?")

    for question in questions:
        console.print(Panel(f"[bold blue]Question:[/bold blue] {question}", expand=False))
        answer = await process_question(question)
        console.print(Panel(f"[bold green]Answer:[/bold green] {answer}", expand=False))

        if show_state:
            console.print("\n[bold]State Information:[/bold]")
            print_state_info(
                graph.get_global_state(),
                analysis_node.get_state(),
                search_node.get_state(),
                answer_node.get_state(),
            )

        console.print("\n" + "=" * 80 + "\n")

    console.print(
        "[bold yellow]All questions processed. Thank you for using SmartGraph![/bold yellow]"
    )


if __name__ == "__main__":
    asyncio.run(main())
