# smartgraph/components/branching_component.py

from typing import Any, Callable, Dict, List

from ..core import ReactiveComponent
from ..logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class BranchingComponent(ReactiveComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.branches: List[Dict[str, Any]] = []
        self.default_branch: ReactiveComponent = None

    def add_branch(
        self, condition: Callable[[Any], bool], component: ReactiveComponent, branch_name: str
    ):
        """Add a new branch with a condition, component, and name."""
        self.branches.append({"condition": condition, "component": component, "name": branch_name})

    def set_default_branch(self, component: ReactiveComponent):
        """Set the default branch to be used when no conditions are met."""
        self.default_branch = component

    async def process(self, input_data: Any) -> Dict[str, Any]:
        logger.info(f"BranchingComponent {self.name} received: {input_data}")

        try:
            for branch in self.branches:
                if branch["condition"](input_data):
                    logger.info(f"BranchingComponent {self.name} taking branch: {branch['name']}")
                    # Pass only the 'content' if the input_data is a dictionary
                    process_input = (
                        input_data["content"] if isinstance(input_data, dict) else input_data
                    )
                    result = await branch["component"].process({"message": process_input})
                    return {"branch": branch["name"], "result": result}

            # If no condition is met, use the default branch
            if self.default_branch:
                logger.info(f"BranchingComponent {self.name} taking default branch")
                process_input = (
                    input_data["content"] if isinstance(input_data, dict) else input_data
                )
                result = await self.default_branch.process({"message": process_input})
                return {"branch": "default", "result": result}
            else:
                logger.warning(
                    f"BranchingComponent {self.name} no matching branch and no default set"
                )
                return {"branch": "none", "result": input_data}

        except Exception as e:
            logger.error(f"Error in BranchingComponent {self.name}: {str(e)}", exc_info=True)
            return {"error": str(e)}
