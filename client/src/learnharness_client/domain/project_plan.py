"""A child's project idea and to-do list. The child decides what goes on the list."""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_DESCRIPTION = 2000
MAX_QUESTION = 1000
MAX_TODOS = 30
MAX_TODO_LENGTH = 120
MAX_SUGGESTIONS = 8


def clean_todo(text: str) -> str:
    return " ".join(text.split())[:MAX_TODO_LENGTH].strip()


@dataclass(slots=True)
class TodoItem:
    text: str
    done: bool = False


@dataclass(slots=True)
class ProjectPlan:
    description: str = ""
    todos: list[TodoItem] = field(default_factory=list)
    question: str = ""  # the helper's last question, so the child can answer it later
    suggestions: list[str] = field(default_factory=list)  # not on the list until accepted

    def has_todo(self, text: str, *, ignore: TodoItem | None = None) -> bool:
        wanted = clean_todo(text).casefold()
        return any(item is not ignore and item.text.casefold() == wanted for item in self.todos)

    def add_todo(self, text: str) -> bool:
        clean = clean_todo(text)
        if not clean or len(self.todos) >= MAX_TODOS or self.has_todo(clean):
            return False
        self.todos.append(TodoItem(clean))
        return True

    def set_suggestions(self, suggestions: list[str]) -> None:
        fresh: list[str] = []
        for text in suggestions:
            clean = clean_todo(text)
            known = {item.casefold() for item in fresh}
            if clean and clean.casefold() not in known and not self.has_todo(clean):
                fresh.append(clean)
        self.suggestions = fresh[:MAX_SUGGESTIONS]

    def accept_suggestion(self, text: str) -> bool:
        """False when the list is full; the suggestion then stays available."""
        if text not in self.suggestions:
            return False
        if not self.has_todo(text) and not self.add_todo(text):
            return False
        self.suggestions.remove(text)
        return True

    def done_count(self) -> int:
        return sum(item.done for item in self.todos)

    def to_dict(self) -> dict[str, object]:
        return {
            "description": self.description,
            "todos": [{"text": item.text, "done": item.done} for item in self.todos],
            "question": self.question,
            "suggestions": list(self.suggestions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ProjectPlan:
        """Tolerates damaged settings: whatever cannot be read is left out."""
        description = data.get("description")
        question = data.get("question")
        plan = cls(
            description=description[:MAX_DESCRIPTION] if isinstance(description, str) else "",
            question=question[:MAX_QUESTION] if isinstance(question, str) else "",
        )
        todos = data.get("todos")
        for entry in todos if isinstance(todos, list) else []:
            readable = isinstance(entry, dict) and isinstance(entry.get("text"), str)
            if readable and plan.add_todo(entry["text"]):
                plan.todos[-1].done = entry.get("done") is True
        suggestions = data.get("suggestions")
        if isinstance(suggestions, list):
            plan.set_suggestions([item for item in suggestions if isinstance(item, str)])
        return plan
