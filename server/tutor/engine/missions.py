"""Planning and running missions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from learnharness_protocol import LearningResponse, Mission, MissionStep, StudentMessage

from children.models import LearningMission

from .. import harness
from ..models import ExerciseRecord
from .tasks import Response, _error


class TutorMissions:
    """Missions."""

    def _plan_mission(self, message: StudentMessage) -> Response:
        levels = self._topic_levels()
        # Without a wish of its own the child follows the learning order.
        topics = (
            harness.reachable_topics(levels)
            if message.mission_from_project
            else list(harness.MISSION_TOPICS)
        )
        extra = harness.topic_levels(levels)
        if message.mission_from_project:
            extra += (
                "\n\nDas Kind hat keinen eigenen Wunsch genannt. Wähle selbst den nächsten "
                "Baustein für <projekt> mit einem dieser Themen: " + ", ".join(topics)
            )

        def build(data: dict[str, Any]) -> tuple[Mission, str]:
            try_title = (
                "Starte dein Programm"
                if message.language == "python"
                else "Probiere es in Godot aus"
            )
            steps_data = harness.check_mission_plan(data, topics, try_title)
            mission = Mission(
                id=f"wunsch-{uuid4().hex[:10]}",
                title=str(data.get("title", "Deine Mission"))[:120] or "Deine Mission",
                goal=str(data.get("goal", "")),
                skill=data["skill"],
                steps=[
                    MissionStep(id=f"s{index}", title=str(step["title"])[:200], kind=step["kind"])
                    for index, step in enumerate(steps_data, start=1)
                ],
            )
            text, _ = harness.filter_text(
                str(data.get("message", "")), self.settings.max_code_lines_in_chat
            )
            return mission, text.strip()

        prompt = harness.user_prompt(message, extra=extra)
        (mission, text), _ = self._call_json(
            "mission",
            self._system("mission", message),
            [{"role": "user", "content": prompt}],
            harness.mission_schema(topics),
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
        extra = harness.mission_step_context(mission, step)
        if step.note:
            extra += f"\nHinweis der Lehrkraft für diesen Schritt: {step.note}"
        topic = mission.skill if mission.skill in harness.MISSION_TOPICS else None
        stage = self._start_topic(topic)
        extra += "\n\n" + harness.known_topics_note(self._topic_levels(), topic)
        built = self._exercise_round(
            "mission_step",
            message,
            extra=extra,
            allow_code=step.kind == "exercise",
            prefix=f"mission_{mission.id}_{step.id}",
            stage=stage,
            topic=topic,
        )
        return LearningResponse(mode="exercise", message=built.message, exercise=built.exercise)

    def _topic_levels(self) -> dict[str, int]:
        child = self.session.child
        if child is None:
            return {}
        rows = child.skills.filter(skill_id__in=harness.MISSION_TOPICS)
        return {row.skill_id: row.level for row in rows}

    def _start_topic(self, topic: str | None) -> int:
        """The child's stage; the first step of a topic marks it as started."""
        level = self._topic_levels().get(topic or "", 0)
        child = self.session.child
        if child is not None and topic is not None and level < 1:
            child.set_skill(topic, harness.SKILLS[topic], 1)
        return harness.stage_for(level)

    def _advance_topic(self, topic: str) -> None:
        """The next stage starts after enough exercises of this stage solved at the first try."""
        child = self.session.child
        if child is None or topic not in harness.MISSION_TOPICS:
            self._raise_skill(topic)
            return
        row = child.skills.filter(skill_id=topic).first()
        if row is None or row.level < 1:
            child.set_skill(topic, harness.SKILLS[topic], 1)
            return
        if row.level >= 3:
            return
        solved = ExerciseRecord.objects.filter(
            session__child=child,
            intent="mission_step",
            skill_id=topic,
            solved_at__gte=row.updated_at,
            wrong_attempts=0,  # guessing until it fits does not count
        )
        count = sum(record.exercise.get("difficulty") == row.level for record in solved)
        if count >= harness.STAGE_UP_AFTER:
            child.set_skill(topic, harness.SKILLS[topic], row.level + 1)
