from __future__ import annotations


class SmartGraphException(Exception):
    """Base exception class for all SmartGraph-related exceptions."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ExecutionError(SmartGraphException):
    """Exception raised when there's an error during the execution of a SmartGraph node or workflow."""

    def __init__(self, message: str, node_id: str | None = None):
        self.node_id = node_id
        super().__init__(f"Execution error{'in node ' + node_id if node_id else ''}: {message}")


class ConfigurationError(SmartGraphException):
    """Exception raised when there's an error in the configuration of SmartGraph components."""

    def __init__(self, message: str, component: str | None = None):
        self.component = component
        super().__init__(f"Configuration error{'in ' + component if component else ''}: {message}")


class ValidationError(SmartGraphException):
    """Exception raised when there's a validation error in SmartGraph inputs or outputs."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(f"Validation error{'for ' + field if field else ''}: {message}")


class MemoryError(SmartGraphException):
    """Exception raised when there's an error related to memory management in SmartGraph."""

    def __init__(self, message: str, memory_type: str | None = None):
        self.memory_type = memory_type
        super().__init__(f"Memory error{'in ' + memory_type if memory_type else ''}: {message}")


class GraphStructureError(SmartGraphException):
    """Exception raised when there's an error in the structure of the SmartGraph."""

    def __init__(self, message: str):
        super().__init__(f"Graph structure error: {message}")


class ActorExecutionError(SmartGraphException):
    """Exception raised when there's an error during the execution of an actor's task."""

    def __init__(self, message: str, actor_name: str | None = None):
        self.actor_name = actor_name
        super().__init__(
            f"Actor execution error{'for ' + actor_name if actor_name else ''}: {message}"
        )
