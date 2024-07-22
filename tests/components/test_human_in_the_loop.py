import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from reactivex import Observable, Subject

from smartgraph import ReactiveAIComponent
from smartgraph.components.human_in_the_loop import (
    BasicApprovalComponent,
    CorrectionRefinementComponent,
    GuidedDecisionMakingComponent,
    IterativeFeedbackComponent,
)


@pytest.fixture
def human_in_the_loop():
    return BasicApprovalComponent("test_component")

class TestHumanInTheLoopComponent:
    @pytest.mark.asyncio
    async def test_submit_human_input(self, human_in_the_loop):
        input_data = "Test input"
        human_in_the_loop.submit_human_input(input_data)
        assert human_in_the_loop.human_input_value == input_data
        assert human_in_the_loop.human_input_event.is_set()

    def test_get_system_output_observable(self, human_in_the_loop):
        observable = human_in_the_loop.get_system_output_observable()
        assert isinstance(observable, Observable)

    def test_get_final_output_observable(self, human_in_the_loop):
        observable = human_in_the_loop.get_final_output_observable()
        assert isinstance(observable, Observable)

    @pytest.mark.asyncio
    async def test_get_human_input_timeout(self, human_in_the_loop):
        with patch.object(human_in_the_loop, '_get_human_input', return_value=None):
            result = await human_in_the_loop.process("Test input")
            assert result is not None
            assert "error" in result

    @pytest.mark.asyncio
    async def test_process_error_handling(self, human_in_the_loop):
        with patch.object(human_in_the_loop, '_generate_system_output', side_effect=Exception("Test error")):
            result = await human_in_the_loop.process("Test input")
            assert "error" in result
            assert "Test error" in result["error"]

class TestBasicApprovalComponent:
    @pytest.fixture
    def basic_approval(self):
        return BasicApprovalComponent("basic_approval")

    @pytest.mark.asyncio
    async def test_generate_system_output(self, basic_approval):
        input_data = "Test input"
        result = await basic_approval._generate_system_output(input_data)
        assert isinstance(result, dict)
        assert "decision" in result
        assert "data" in result
        assert result["data"] == input_data

    @pytest.mark.asyncio
    async def test_process_human_input_approved(self, basic_approval):
        system_output = {"decision": "Proposed action", "data": "Test data"}
        result = await basic_approval._process_human_input(True, system_output)
        assert result == {"status": "approved", "action": "Proposed action"}

    @pytest.mark.asyncio
    async def test_process_human_input_rejected(self, basic_approval):
        system_output = {"decision": "Proposed action", "data": "Test data"}
        result = await basic_approval._process_human_input(False, system_output)
        assert result == {"status": "rejected", "action": None}

    @pytest.mark.asyncio
    async def test_process_error_handling(self, basic_approval):  # or basic_approval, correction_refinement, etc.
        with patch.object(basic_approval, '_generate_system_output', side_effect=Exception("Test error")):
            result = await basic_approval.process("Test input")
            assert "error" in result
            assert "Test error" in result["error"]

class TestCorrectionRefinementComponent:
    @pytest.fixture
    def correction_refinement(self):
        return CorrectionRefinementComponent("correction_refinement")

    @pytest.mark.asyncio
    async def test_generate_system_output(self, correction_refinement):
        input_data = "Test input"
        result = await correction_refinement._generate_system_output(input_data)
        assert result == "Initial output based on: Test input"

    @pytest.mark.asyncio
    async def test_process_human_input(self, correction_refinement):
        human_input = "Corrected output"
        system_output = "Initial output"
        result = await correction_refinement._process_human_input(human_input, system_output)
        assert result == "Refined output: Corrected output"
    @pytest.mark.asyncio
    async def test_process_error_handling(self, correction_refinement):
            with patch.object(correction_refinement, '_generate_system_output', side_effect=Exception("Test error")):
                result = await correction_refinement.process("Test input")
                assert "error" in result
                assert "Test error" in result["error"]

class TestGuidedDecisionMakingComponent:
    @pytest.fixture
    def guided_decision(self):
        return GuidedDecisionMakingComponent("guided_decision")

    @pytest.mark.asyncio
    async def test_generate_system_output(self, guided_decision):
        input_data = "Test input"
        result = await guided_decision._generate_system_output(input_data)
        assert isinstance(result, dict)
        assert "options" in result
        assert len(result["options"]) == 2
        assert all(["name" in option and "pros" in option and "cons" in option for option in result["options"]])

    @pytest.mark.asyncio
    async def test_process_human_input(self, guided_decision):
        human_input = "Option A"
        system_output = {
            "options": [
                {"name": "Option A", "pros": ["Pro 1", "Pro 2"], "cons": ["Con 1"]},
                {"name": "Option B", "pros": ["Pro 1"], "cons": ["Con 1", "Con 2"]},
            ]
        }
        result = await guided_decision._process_human_input(human_input, system_output)
        assert result == {"selected_option": "Option A", "original_options": system_output["options"]}
    @pytest.mark.asyncio
    async def test_process_error_handling(self, guided_decision):
            with patch.object(guided_decision, '_generate_system_output', side_effect=Exception("Test error")):
                result = await guided_decision.process("Test input")
                assert "error" in result
                assert "Test error" in result["error"]
class TestIterativeFeedbackComponent:
    @pytest.fixture
    def iterative_feedback(self):
        return IterativeFeedbackComponent("iterative_feedback")

    @pytest.mark.asyncio
    async def test_generate_system_output(self, iterative_feedback):
        input_data = "Test input"
        result = await iterative_feedback._generate_system_output(input_data)
        assert result == {"iteration": 1, "output": "Initial output for: Test input"}

    @pytest.mark.asyncio
    async def test_process_human_input(self, iterative_feedback):
        human_input = {"feedback": "Refined content"}
        system_output = {"iteration": 1, "output": "Initial output"}
        result = await iterative_feedback._process_human_input(human_input, system_output)
        assert result == {"iteration": 2, "output": "Refined output (iteration 2): Refined content"}

    @pytest.mark.asyncio
    async def test_process_multiple_iterations(self, iterative_feedback):
        input_data = "Test input"
        result = await iterative_feedback._generate_system_output(input_data)

        for i in range(2, 4):
            human_input = {"feedback": f"Iteration {i} feedback"}
            result = await iterative_feedback._process_human_input(human_input, result)
            assert result["iteration"] == i
            assert result["output"] == f"Refined output (iteration {i}): Iteration {i} feedback"

    @pytest.mark.asyncio
    async def test_process_complete_flag(self, iterative_feedback):
        input_data = "Test input"
        human_inputs = [
            {"feedback": "First iteration"},
            {"feedback": "Second iteration"},
            {"feedback": "Final iteration", "complete": True}
        ]

        async def simulate_human_input():
            for input_data in human_inputs:
                await asyncio.sleep(0.1)
                iterative_feedback.submit_human_input(input_data)

        input_task = asyncio.create_task(simulate_human_input())
        result = await iterative_feedback.process(input_data)
        await input_task

        assert result["iteration"] == 3
        assert "Final iteration" in result["output"]

    @pytest.mark.asyncio
    async def test_process_error_handling(self, iterative_feedback):
        with patch.object(iterative_feedback, '_generate_system_output', side_effect=Exception("Test error")):
            result = await iterative_feedback.process("Test input")
            assert "error" in result
            assert "Test error" in result["error"]
            assert "Error in" in result["error"]


@pytest.mark.parametrize("component_class", [
    BasicApprovalComponent,
    CorrectionRefinementComponent,
    GuidedDecisionMakingComponent,
    IterativeFeedbackComponent
])
def test_reactive_ai_component_integration(component_class):
    component = component_class("test")
    assert isinstance(component, ReactiveAIComponent)
    assert hasattr(component, 'input')
    assert hasattr(component, 'output')
    assert callable(component.process)

@pytest.mark.asyncio
async def test_async_workflow(human_in_the_loop):
    async def simulate_human_input(delay, input_data):
        await asyncio.sleep(delay)
        human_in_the_loop.submit_human_input(input_data)

    input_task = asyncio.create_task(simulate_human_input(0.1, "Human decision"))
    process_task = asyncio.create_task(human_in_the_loop.process("Test input"))

    result = await process_task
    await input_task

    assert result is not None