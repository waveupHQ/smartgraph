from typing import Any, Dict, List


def list_append_reducer(old_value: List[Any], new_value: Any) -> List[Any]:
    return old_value + [new_value]


def max_reducer(old_value: int, new_value: int) -> int:
    return max(old_value, new_value)


def dict_update_reducer(old_value: Dict[str, Any], new_value: Dict[str, Any]) -> Dict[str, Any]:
    old_value.update(new_value)
    return old_value
