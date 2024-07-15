import pytest

from smartgraph.condition_evaluator import ConditionEvaluator


def test_evaluate_single_condition():
    condition = lambda data: data.get("x") > 5
    assert ConditionEvaluator.evaluate([condition], {"x": 10}) == True
    assert ConditionEvaluator.evaluate([condition], {"x": 3}) == False


def test_evaluate_multiple_conditions():
    conditions = [lambda data: data.get("x") > 5, lambda data: data.get("y") < 10]
    assert ConditionEvaluator.evaluate(conditions, {"x": 7, "y": 8}) == True
    assert ConditionEvaluator.evaluate(conditions, {"x": 7, "y": 12}) == False
    assert ConditionEvaluator.evaluate(conditions, {"x": 3, "y": 8}) == False


def test_create_condition():
    condition = ConditionEvaluator.create_condition("key", "value")
    assert condition({"key": "value"}) == True
    assert condition({"key": "other_value"}) == False
    assert condition({"other_key": "value"}) == False


def test_create_range_condition():
    condition = ConditionEvaluator.create_range_condition("num", 0, 10)
    assert condition({"num": 5}) == True
    assert condition({"num": 0}) == True
    assert condition({"num": 10}) == True
    assert condition({"num": -1}) == False
    assert condition({"num": 11}) == False
    assert condition({"other_num": 5}) == False
