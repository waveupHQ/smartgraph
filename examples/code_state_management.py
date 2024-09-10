import asyncio
import random
from typing import Any, Dict

from smartgraph import ReactiveComponent, ReactiveSmartGraph


class VocabularyBank(ReactiveComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.create_state(
            "words",
            {
                "easy": ["cat", "dog", "house", "tree", "book"],
                "medium": ["mountain", "computer", "elephant", "birthday", "adventure"],
                "hard": ["serendipity", "eloquent", "ephemeral", "ubiquitous", "paradigm"],
            },
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        difficulty = input_data.get("difficulty", "easy")
        words = self.get_state("words").value
        return {"word": random.choice(words[difficulty]), **input_data}


class DifficultyManager(ReactiveComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.create_state("current_difficulty", "easy")
        self.create_state("correct_streak", 0)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")
        if action == "get_word":
            return {"difficulty": self.get_state("current_difficulty").value, **input_data}
        elif action == "process_answer":
            correct = input_data.get("correct", False)
            current_difficulty = self.get_state("current_difficulty").value
            streak = self.get_state("correct_streak").value

            if correct:
                streak += 1
                if streak >= 3 and current_difficulty != "hard":
                    current_difficulty = "medium" if current_difficulty == "easy" else "hard"
                    streak = 0
            else:
                streak = 0
                if current_difficulty != "easy":
                    current_difficulty = "easy" if current_difficulty == "hard" else "medium"

            self.update_state("current_difficulty", current_difficulty)
            self.update_state("correct_streak", streak)
            return {"difficulty": current_difficulty, "streak": streak, **input_data}
        return input_data


class UserProgressTracker(ReactiveComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.create_state("total_words", 0)
        self.create_state("correct_words", 0)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")
        if action == "process_answer":
            correct = input_data.get("correct", False)
            total = self.get_state("total_words").value + 1
            correct_count = self.get_state("correct_words").value + (1 if correct else 0)

            self.update_state("total_words", total)
            self.update_state("correct_words", correct_count)

            return {
                "progress": {
                    "total": total,
                    "correct": correct_count,
                    "accuracy": (correct_count / total) * 100 if total > 0 else 0,
                },
                **input_data,
            }
        return input_data


class LanguageLearningApp(ReactiveSmartGraph):
    def __init__(self):
        super().__init__()
        pipeline = self.create_pipeline("LanguageLearning")

        pipeline.add_component(DifficultyManager("Difficulty"))
        pipeline.add_component(VocabularyBank("Vocabulary"))
        pipeline.add_component(UserProgressTracker("Progress"))

        self.compile()

    async def get_word(self) -> str:
        result = await self.execute_and_await("LanguageLearning", {"action": "get_word"})
        return result.get("word", "")

    async def process_answer(self, correct: bool) -> Dict[str, Any]:
        result = await self.execute_and_await(
            "LanguageLearning", {"action": "process_answer", "correct": correct}
        )
        return result


async def main():
    app = LanguageLearningApp()

    for _ in range(10):  # Simulate 10 rounds
        word = await app.get_word()
        print(f"\nTranslate this word: {word}")
        user_input = input("Your translation: ")

        # Simulate checking the answer (in a real app, you'd have actual translation checking)
        correct = random.choice([True, False])
        print("Correct!" if correct else "Incorrect.")

        result = await app.process_answer(correct)
        print(f"New difficulty: {result.get('difficulty', 'N/A')}")
        progress = result.get("progress", {})
        print(
            f"Progress: {progress.get('correct', 0)}/{progress.get('total', 0)} "
            f"({progress.get('accuracy', 0):.2f}% accuracy)"
        )


if __name__ == "__main__":
    asyncio.run(main())
