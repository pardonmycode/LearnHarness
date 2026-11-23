"""A child's project description and the conversation that makes it clearer."""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_DESCRIPTION = 2000
MAX_QUESTION = 1000
MAX_ANSWER = 1000
MAX_TURNS = 12
MAX_SKIPPED = 8
MAX_FINISHED_MISSIONS = 30
MAX_MISSION_TITLE = 120


@dataclass(slots=True)
class PlanTurn:
    question: str
    answer: str


@dataclass(slots=True)
class ProjectPlan:
    description: str = ""
    question: str = ""  # the helper's open question, so the child can answer it later
    suggestion: str = ""  # a better description; only used when the child accepts it
    ready: bool = False  # the helper knows enough to start building
    turns: list[PlanTurn] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # questions the child did not want
    finished_missions: list[str] = field(default_factory=list)
    # To-dos of older versions are kept untouched in the saved data.
    old_todos: object = None

    def add_turn(self, question: str, answer: str) -> None:
        question, answer = question.strip()[:MAX_QUESTION], answer.strip()[:MAX_ANSWER]
        if question and answer:
            self.turns = [*self.turns, PlanTurn(question, answer)][-MAX_TURNS:]

    def add_skipped(self, question: str) -> None:
        clean = question.strip()[:MAX_QUESTION]
        if clean and clean not in self.skipped:
            self.skipped = [*self.skipped, clean][-MAX_SKIPPED:]

    def forget_talk(self) -> None:
        self.question = ""
        self.suggestion = ""
        self.ready = False
        self.turns = []
        self.skipped = []

    def add_finished_mission(self, title: str) -> None:
        clean = " ".join(title.split())[:MAX_MISSION_TITLE].strip()
        if clean and clean not in self.finished_missions:
            self.finished_missions = [*self.finished_missions, clean][-MAX_FINISHED_MISSIONS:]

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "description": self.description,
            "question": self.question,
            "suggestion": self.suggestion,
            "ready": self.ready,
            "turns": [{"question": t.question, "answer": t.answer} for t in self.turns],
            "skipped": list(self.skipped),
            "finished_missions": list(self.finished_missions),
        }
        if self.old_todos is not None:
            data["todos"] = self.old_todos
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ProjectPlan:
        """Tolerates damaged settings: whatever cannot be read is left out."""
        description = data.get("description")
        question = data.get("question")
        suggestion = data.get("suggestion")
        plan = cls(
            description=description[:MAX_DESCRIPTION] if isinstance(description, str) else "",
            question=question[:MAX_QUESTION] if isinstance(question, str) else "",
            suggestion=suggestion[:MAX_DESCRIPTION] if isinstance(suggestion, str) else "",
            ready=data.get("ready") is True,
            old_todos=data.get("todos"),
        )
        turns = data.get("turns")
        for entry in turns if isinstance(turns, list) else []:
            if isinstance(entry, dict):
                asked, answered = entry.get("question"), entry.get("answer")
                if isinstance(asked, str) and isinstance(answered, str):
                    plan.add_turn(asked, answered)
        skipped = data.get("skipped")
        for question in skipped if isinstance(skipped, list) else []:
            if isinstance(question, str):
                plan.add_skipped(question)
        missions = data.get("finished_missions")
        for title in missions if isinstance(missions, list) else []:
            if isinstance(title, str):
                plan.add_finished_mission(title)
        return plan
