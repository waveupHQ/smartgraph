from typing import Any, Callable, Dict


class StateManager:
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._reducers: Dict[str, Callable[[Any, Any], Any]] = {}

    def update_state(self, key: str, value: Any) -> None:
        if key in self._reducers:
            self._state[key] = self._reducers[key](self._state.get(key), value)
        else:
            self._state[key] = value

    def get_state(self, key: str) -> Any:
        return self._state.get(key)

    def set_reducer(self, key: str, reducer: Callable[[Any, Any], Any]) -> None:
        self._reducers[key] = reducer

    def get_full_state(self) -> Dict[str, Any]:
        return self._state.copy()

    def set_full_state(self, state: Dict[str, Any]) -> None:
        self._state = state.copy()

    def clear_state(self) -> None:
        self._state.clear()
