"""Planning and running missions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from learnharness_protocol import LearningResponse, Mission, MissionStep, StudentMessage

from children.models import LearningMission

from .. import harness
from .tasks import Response, _error


class TutorMissions:
    """Missions."""

    def _plan_mission(self, message: StudentMessage) -> Response:
        def build(data: dict[str, Any]) -> tuple[Mission, str]:
            steps_data = [step for step in data.get("steps", []) if step.get("title")][:7]
            if len(steps_data) < 2:
                raise harness.HarnessRejected("Mission braucht mindestens zwei Schritte")
            if steps_data[-1].get("kind") != "try":
                title = (
                    "Starte dein Programm"
                    if message.language == "python"
                    else "Probiere es in Godot aus"
                )
                steps_data.append({"title": title, "kind": "try"})
            mission = Mission(
                id=f"wunsch-{uuid4().hex[:10]}",
                title=str(data.get("title", "Deine Mission"))[:120] or "Deine Mission",
                goal=str(data.get("goal", "")),
                skill=data.get("skill") if data.get("skill") in harness.SKILLS else None,
                steps=[
                    MissionStep(id=f"s{index}", title=str(step["title"])[:200], kind=step["kind"])
                    for index, step in enumerate(steps_data, start=1)
                ],
            )
            text, _ = harness.filter_text(
                str(data.get("message", "")), self.settings.max_code_lines_in_chat
            )
            return mission, text.strip()

        prompt = harness.user_prompt(message)
        (mission, text), _ = self._call_json(
            "mission",
            self._system("mission", message),
            [{"role": "user", "content": prompt}],
            harness.MISSION_SCHEMA,
            build,
        )
        self.session.wish_missions = {
            **self.session.wish_missions,
            mission.id: mission.model_dump(mode="json"),
        }
        self.session.save(update_fields=["wish_missions"])
        return LearningResponse(
            mode="mission", message=text or f"Deine Mission: {mission.title}", mission=mission
        )

    def _find_mission(self, mission_id: str) -> Mission | None:
        stored = LearningMission.objects.prefetch_related("steps").filter(
            mission_id=mission_id, active=True
        )
        if stored:
            return stored[0].to_protocol(with_notes=True)
        data = self.session.wish_missions.get(mission_id)
        return Mission.model_validate(data) if data else None

    def _mission_step(self, message: StudentMessage) -> Response:
        mission = self._find_mission(message.mission_id or "")
        step = (
            next((s for s in mission.steps if s.id == message.mission_step_id), None)
            if mission
            else None
        )
        if mission is None or step is None:
            return _error("unknown_step", "Diesen Missionsschritt kenne ich nicht.")
        if step.kind == "try":
            return LearningResponse(
                mode="explanation",
                message=(
                    "Speichere dein Skript und starte dein Programm."
                    if message.language == "python"
                    else "Speichere dein Skript und probiere es in Godot aus (F5)."
                ),
            )
        extra = (
            f"Mission: {mission.title} – {mission.goal}\n"
            f"Aktueller Schritt: {step.title} (Art: {step.kind})"
        )
        if step.note:
            extra += f"\nHinweis der Lehrkraft für diesen Schritt: {step.note}"
        built = self._exercise_round(
            "mission_step",
            message,
            extra=extra,
            allow_code=step.kind == "exercise",
            prefix=f"mission_{mission.id}_{step.id}",
        )
        return LearningResponse(mode="exercise", message=built.message, exercise=built.exercise)
