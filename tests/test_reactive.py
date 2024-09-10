# tests/test_reactive.py

import pytest
from reactivex import Observable
from reactivex import operators as ops
from reactivex.subject import BehaviorSubject
from reactivex.testing import ReactiveTest, TestScheduler

# Convenience aliases for ReactiveTest methods
on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error


def test_behavior_subject():
    """Test the BehaviorSubject, which emits its initial value to new subscribers."""
    scheduler = TestScheduler()

    def create():
        return BehaviorSubject(10)

    results = scheduler.start(create)

    # BehaviorSubject emits its initial value (10) immediately upon subscription at 200ms
    assert results.messages == [on_next(200, 10)]


def test_map_operator():
    """Test the map operator, which transforms each value emitted by the source Observable."""
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(on_next(250, 5), on_next(350, 10), on_completed(400))

    def create():
        return source.pipe(ops.map(lambda x: x * 2))  # Double each emitted value

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, 10),  # 5 * 2
        on_next(350, 20),  # 10 * 2
        on_completed(400),
    ]


def test_filter_operator():
    """Test the filter operator, which only emits values that satisfy a predicate."""
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(
        on_next(250, 2), on_next(300, 5), on_next(350, 8), on_completed(400)
    )

    def create():
        return source.pipe(ops.filter(lambda x: x > 3))  # Only emit values greater than 3

    results = scheduler.start(create)

    assert results.messages == [on_next(300, 5), on_next(350, 8), on_completed(400)]


def test_merge():
    """Test the merge operator, which combines multiple Observables into one."""
    scheduler = TestScheduler()
    source1 = scheduler.create_hot_observable(on_next(250, 1), on_next(350, 3), on_completed(400))
    source2 = scheduler.create_hot_observable(on_next(300, 2), on_next(400, 4), on_completed(450))

    def create():
        return source1.pipe(ops.merge(source2))  # Merge emissions from source1 and source2

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, 1),
        on_next(300, 2),
        on_next(350, 3),
        on_next(400, 4),
        on_completed(450),  # Completes when both sources have completed
    ]


def test_combine_latest():
    """Test the combine_latest operator, which combines the latest values from multiple Observables."""
    scheduler = TestScheduler()
    source1 = scheduler.create_hot_observable(on_next(250, 1), on_next(350, 3), on_completed(400))
    source2 = scheduler.create_hot_observable(
        on_next(300, "a"), on_next(400, "b"), on_completed(450)
    )

    def create():
        return source1.pipe(
            ops.combine_latest(source2)  # Combine latest values from source1 and source2
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(300, (1, "a")),  # First combined emission when source2 emits 'a'
        on_next(350, (3, "a")),  # Updated when source1 emits 3
        on_next(400, (3, "b")),  # Updated when source2 emits 'b'
        on_completed(450),  # Completes when both sources have completed
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
