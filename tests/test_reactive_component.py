# tests/test_reactive_component.py

import pytest
from reactivex import operators as ops
from reactivex.testing import ReactiveTest, TestScheduler

from smartgraph.core import ReactiveComponent

# Convenience aliases for ReactiveTest methods
on_next = ReactiveTest.on_next
on_completed = ReactiveTest.on_completed
on_error = ReactiveTest.on_error


class TestReactiveComponent:
    def test_component_creation(self):
        component = ReactiveComponent("TestComponent")
        assert component.name == "TestComponent"

    def test_process_input(self):
        scheduler = TestScheduler()

        class TestComponent(ReactiveComponent):
            def process(self, input_data):
                return input_data * 2

        component = TestComponent("DoubleComponent")

        def create():
            return component.output

        # Create a hot observable to simulate input
        source = scheduler.create_hot_observable(
            on_next(300, 5), on_next(400, 10), on_completed(500)
        )

        # Subscribe the source to the component's input
        source.subscribe(component.input)

        results = scheduler.start(create)

        assert results.messages == [
            on_next(300, 10),  # 5 * 2
            on_next(400, 20),  # 10 * 2
        ]

    def test_error_handling(self):
        scheduler = TestScheduler()

        class ErrorComponent(ReactiveComponent):
            def process(self, input_data):
                raise ValueError("Test error")

        component = ErrorComponent("ErrorComponent")

        def create():
            return component.error

        source = scheduler.create_hot_observable(on_next(300, "test"), on_completed(400))

        source.subscribe(component.input)

        results = scheduler.start(create)

        assert len(results.messages) == 1
        assert results.messages[0].time == 300
        assert isinstance(results.messages[0].value.value, ValueError)
        assert str(results.messages[0].value.value) == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
