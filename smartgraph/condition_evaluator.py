from typing import Any, Callable, Dict, List


class ConditionEvaluator:
    @staticmethod
    def evaluate(conditions: List[Callable[[Dict[str, Any]], bool]], data: Dict[str, Any]) -> bool:
        """Evaluate a list of conditions against the provided data.

        Args:
            conditions (List[Callable[[Dict[str, Any]], bool]]): List of condition functions.
            data (Dict[str, Any]): Data to evaluate the conditions against.

        Returns:
            bool: True if all conditions are met, False otherwise.
        """
        return all(condition(data) for condition in conditions)

    @staticmethod
    def create_condition(key: str, value: Any) -> Callable[[Dict[str, Any]], bool]:
        """Create a simple condition function that checks if a key in the data matches a specific value.

        Args:
            key (str): The key to check in the data dictionary.
            value (Any): The value to compare against.

        Returns:
            Callable[[Dict[str, Any]], bool]: A condition function.
        """
        return lambda data: data.get(key) == value

    @staticmethod
    def create_range_condition(
        key: str, min_value: float, max_value: float
    ) -> Callable[[Dict[str, Any]], bool]:
        """Create a condition function that checks if a numeric value is within a specified range.

        Args:
            key (str): The key to check in the data dictionary.
            min_value (float): The minimum value of the range (inclusive).
            max_value (float): The maximum value of the range (inclusive).

        Returns:
            Callable[[Dict[str, Any]], bool]: A condition function.
        """
        return lambda data: min_value <= data.get(key, float("-inf")) <= max_value
