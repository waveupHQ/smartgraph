from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from .base import BaseActor, Task
from .exceptions import ExecutionError
from .state_manager import StateManager

if TYPE_CHECKING:
    from .core import Node  # Import Node only for type checking


class TaskExecutor:
    @staticmethod
    async def execute_task(
        actor: BaseActor,
        task: Task,
        input_data: Dict[str, Any],
        state: Dict[str, Any],
        pre_execute: Optional[Callable] = None,
        post_execute: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        if pre_execute:
            input_data = await pre_execute(input_data, state)

        try:
            output = await actor.perform_task(task, input_data, state)
        except Exception as e:
            raise ExecutionError(f"Error executing task: {str(e)}")

        if post_execute:
            output = await post_execute(output, state)

        return output

    @staticmethod
    async def execute_node_task(node: "Node") -> Dict[str, Any]:
        return await TaskExecutor.execute_task(
            node.actor,
            node.task,
            node.input_data,
            node.state_manager.get_full_state(),
            node.pre_execute,
            node.post_execute,
        )
