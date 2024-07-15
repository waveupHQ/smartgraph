import pytest

from smartgraph.state_manager import StateManager


def test_state_manager_update_and_get():
    sm = StateManager()
    sm.update_state("key1", "value1")
    assert sm.get_state("key1") == "value1"


def test_state_manager_reducer():
    sm = StateManager()
    sm.set_reducer("sum", lambda old, new: (old or 0) + new)
    sm.update_state("sum", 5)
    assert sm.get_state("sum") == 5
    sm.update_state("sum", 3)
    assert sm.get_state("sum") == 8


def test_state_manager_full_state():
    sm = StateManager()
    sm.update_state("key1", "value1")
    sm.update_state("key2", "value2")
    full_state = sm.get_full_state()
    assert full_state == {"key1": "value1", "key2": "value2"}


def test_state_manager_set_full_state():
    sm = StateManager()
    new_state = {"key1": "value1", "key2": "value2"}
    sm.set_full_state(new_state)
    assert sm.get_full_state() == new_state


def test_state_manager_clear_state():
    sm = StateManager()
    sm.update_state("key1", "value1")
    sm.clear_state()
    assert sm.get_full_state() == {}
