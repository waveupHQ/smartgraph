# smartgraph/components/human_in_the_loop.py

import asyncio
from typing import Any, Dict, Optional

from reactivex import Observable, Subject

from smartgraph import ReactiveAIComponent
from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class HumanInTheLoopComponent(ReactiveAIComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.human_input_subject = Subject()
        self.system_output_subject = Subject()
        self.final_output_subject = Subject()
        self.human_input_event = asyncio.Event()
        self.human_input_value = None

    async def process(self, input_data: Any) -> Any:
        try:
            system_output = await self._generate_system_output(input_data)
            self.system_output_subject.on_next(system_output)

            human_input = await self._get_human_input(system_output)
            if human_input is None:
                return {"error": "Timeout waiting for human input"}

            final_output = await self._process_human_input(human_input, system_output)
            self.final_output_subject.on_next(final_output)
            return final_output
        except Exception as e:
            error_message = f"Error in {self.name} process: {str(e)}"
            logger.error(error_message)
            return {"error": error_message}

    async def _generate_system_output(self, input_data: Any) -> Any:
        # Implement system logic here
        raise NotImplementedError

    async def _get_human_input(self, system_output: Any, timeout: float = 60.0) -> Any:
        self.human_input_event.clear()
        self.human_input_value = None

        try:
            await asyncio.wait_for(self.human_input_event.wait(), timeout=timeout)
            return self.human_input_value
        except asyncio.TimeoutError:
            return None

    async def _process_human_input(self, human_input: Any, system_output: Any) -> Any:
        # Process human input and generate final output
        raise NotImplementedError

    def submit_human_input(self, input_data: Any):
        self.human_input_value = input_data
        self.human_input_event.set()
        self.human_input_subject.on_next(input_data)

    def get_system_output_observable(self) -> Observable:
        return self.system_output_subject

    def get_final_output_observable(self) -> Observable:
        return self.final_output_subject

    async def _get_human_input(self, system_output: Any, timeout: float = 60.0) -> Any:
        self.human_input_event.clear()
        self.human_input_value = None

        try:
            await asyncio.wait_for(self.human_input_event.wait(), timeout=timeout)
            return self.human_input_value
        except asyncio.TimeoutError:
            return None


class BasicApprovalComponent(HumanInTheLoopComponent):
    async def _generate_system_output(self, input_data: Any) -> Dict[str, Any]:
        # Generate a decision or action for approval
        return {"decision": "Proposed action", "data": input_data}

    async def _process_human_input(
        self, human_input: bool, system_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        if human_input:
            return {"status": "approved", "action": system_output["decision"]}
        else:
            return {"status": "rejected", "action": None}


class CorrectionRefinementComponent(HumanInTheLoopComponent):
    async def _generate_system_output(self, input_data: Any) -> str:
        # Generate initial output
        return f"Initial output based on: {input_data}"

    async def _process_human_input(self, human_input: str, system_output: str) -> str:
        # Incorporate human corrections/refinements
        return f"Refined output: {human_input}"


class GuidedDecisionMakingComponent(HumanInTheLoopComponent):
    async def _generate_system_output(self, input_data: Any) -> Dict[str, Any]:
        # Generate options with pros and cons
        return {
            "options": [
                {"name": "Option A", "pros": ["Pro 1", "Pro 2"], "cons": ["Con 1"]},
                {"name": "Option B", "pros": ["Pro 1"], "cons": ["Con 1", "Con 2"]},
            ]
        }

    async def _process_human_input(
        self, human_input: str, system_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Process the selected option
        return {"selected_option": human_input, "original_options": system_output["options"]}


class IterativeFeedbackComponent(HumanInTheLoopComponent):
    async def _generate_system_output(self, input_data: Any) -> Dict[str, Any]:
        # Generate initial output
        return {"iteration": 1, "output": f"Initial output for: {input_data}"}

    async def _process_human_input(
        self, human_input: Dict[str, Any], system_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Process feedback and generate new output
        new_iteration = system_output["iteration"] + 1
        return {
            "iteration": new_iteration,
            "output": f"Refined output (iteration {new_iteration}): {human_input['feedback']}",
        }

    async def process(self, input_data: Any) -> Any:
        try:
            system_output = await self._generate_system_output(input_data)
            iteration = 1
            while True:
                self.system_output_subject.on_next(system_output)
                human_input = await self._get_human_input(system_output)
                if human_input is None:
                    return {"error": "No human input received"}
                if human_input.get("complete", False):
                    break
                system_output = await self._process_human_input(human_input, system_output)
                iteration += 1
            final_output = {
                "iteration": iteration,
                "output": f"Refined output (iteration {iteration}): {human_input['feedback']}",
            }
            self.final_output_subject.on_next(final_output)
            return final_output
        except Exception as e:
            error_message = f"Error in {self.name} process: {str(e)}"
            logger.error(error_message)
            return {"error": error_message}


# Additional components can be implemented for other patterns...
