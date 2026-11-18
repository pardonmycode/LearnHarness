"""Keep the local child profiles in step with the central administration.

The server is the source of truth for profiles and levels (teachers may lower a level
there). This PC keeps a copy so children can keep learning when the server is away.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from urllib.parse import quote

from learnharness_protocol import ChildProfile, ChildProfileList, LevelUnlock, MissionList
from pydantic import ValidationError

from .config import AppSettings
from .domain.profile import StudentProfile
from .net.admin_client import AdminClient, AdminResponse

LOG = logging.getLogger(__name__)


class SyncResult(Enum):
    DISABLED = "disabled"
    OK = "ok"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"


def _failure(response: AdminResponse) -> SyncResult | None:
    if response.status == 0:
        return SyncResult.OFFLINE
    if response.status in (401, 403):
        return SyncResult.UNAUTHORIZED
    return None


def to_protocol(settings: AppSettings, profile: StudentProfile) -> ChildProfile:
    return ChildProfile(
        profile_id=profile.profile_id,
        pseudonym=profile.pseudonym,
        experience_level=int(profile.experience_level),
        max_level=settings.max_unlocked_learning_level(profile.profile_id),
    )


class AdminSync:
    def __init__(self, settings: AppSettings, client: AdminClient) -> None:
        self.settings = settings
        self.client = client

    @classmethod
    def from_settings(cls, settings: AppSettings) -> AdminSync | None:
        if not settings.admin_enabled:
            return None
        return cls(settings, AdminClient(settings.admin_url, settings.admin_token))

    # Start-up ---------------------------------------------------------------------

    def sync_at_start(self) -> SyncResult:
        """Send what is pending, register new local profiles, then take over the server state."""
        steps = (
            self._send_pending_unlocks,
            self._register_local_profiles,
            self._send_pending_missions,
            self._pull,
        )
        for step in steps:
            result = step()
            if result is not None:
                LOG.info("Profile sync stopped: %s", result.value)
                return result
        return SyncResult.OK

    def _send_pending_unlocks(self) -> SyncResult | None:
        for profile_id, level in self.settings.pending_unlocks.items():
            response = self.client.request_blocking(
                "POST", AdminClient.child_path(profile_id, "unlock/"), LevelUnlock(level=level)
            )
            if (failure := _failure(response)) is not None:
                return failure
            self.settings.clear_pending_unlock(profile_id)
        return None

    def _send_pending_missions(self) -> SyncResult | None:
        for profile_id, mission_id in sorted(self.settings.pending_mission_reports):
            response = self.client.request_blocking("POST", self._done_path(profile_id, mission_id))
            if (failure := _failure(response)) is not None:
                return failure
            # Sent, or the mission/child no longer exists (404): nothing left to retry.
            self.settings.clear_pending_mission_report(profile_id, mission_id)
        return None

    def _register_local_profiles(self) -> SyncResult | None:
        synced = self.settings.synced_profile_ids
        for profile in self.settings.student_profiles:
            if profile.profile_id in synced:
                continue
            response = self.client.request_blocking(
                "POST", "/children/", to_protocol(self.settings, profile)
            )
            if (failure := _failure(response)) is not None:
                return failure
            if response.status == 409:
                # The teacher archived this child: it no longer appears on this PC.
                self.settings.delete_student_profile(profile.profile_id)
                continue
            if response.ok:
                synced.add(profile.profile_id)
        self.settings.set_synced_profile_ids(synced)
        return None

    def _pull(self) -> SyncResult | None:
        group = self.settings.admin_group
        path = "/children/" + (f"?group={quote(group)}" if group else "")
        response = self.client.request_blocking("GET", path)
        if (failure := _failure(response)) is not None:
            return failure
        try:
            listing = ChildProfileList.model_validate(response.data)
        except ValidationError:
            LOG.warning("Invalid profile list from the administration")
            return SyncResult.OFFLINE
        server_ids = {profile.profile_id for profile in listing.profiles}
        for profile in listing.profiles:
            self.apply(profile)
        synced = self.settings.synced_profile_ids
        for profile_id in synced - server_ids:
            # Not in the (possibly group-filtered) list: ask for this child directly.
            detail = self.client.request_blocking("GET", AdminClient.child_path(profile_id))
            if (failure := _failure(detail)) is not None:
                return failure
            if detail.status == 404:
                self.settings.delete_student_profile(profile_id)
                synced.discard(profile_id)
            elif detail.ok:
                self.apply(ChildProfile.model_validate(detail.data))
        self.settings.set_synced_profile_ids(synced | server_ids)
        return None

    def apply(self, profile: ChildProfile) -> None:
        try:
            local = StudentProfile.from_dict(
                {
                    "profile_id": profile.profile_id,
                    "pseudonym": profile.pseudonym,
                    "experience_level": profile.experience_level,
                }
            )
        except (KeyError, ValueError):
            LOG.warning("Skipped a server profile that is not valid on this PC")
            return
        self.settings.save_student_profile(local, remember=False)
        self.settings.set_learning_level(profile.profile_id, profile.max_level)

    # While the app runs ----------------------------------------------------------------

    def register(self, profile: StudentProfile) -> None:
        def done(response: AdminResponse) -> None:
            if response.ok:
                ids = self.settings.synced_profile_ids
                ids.add(profile.profile_id)
                self.settings.set_synced_profile_ids(ids)

        self.client.request("POST", "/children/", to_protocol(self.settings, profile), done)

    def unlock(
        self, profile_id: str, level: int, on_level: Callable[[int], None] | None = None
    ) -> None:
        """Remember the unlock first, so it survives a missing network connection."""
        self.settings.add_pending_unlock(profile_id, level)

        def done(response: AdminResponse) -> None:
            if response.status == 0:
                return
            self.settings.clear_pending_unlock(profile_id)
            if response.ok:
                try:
                    server_level = ChildProfile.model_validate(response.data).max_level
                except ValidationError:
                    return
                self.settings.set_learning_level(profile_id, server_level)
                if on_level is not None:
                    on_level(server_level)

        self.client.request(
            "POST", AdminClient.child_path(profile_id, "unlock/"), LevelUnlock(level=level), done
        )

    def fetch_progress(self, profile_id: str) -> None:
        self.client.fetch_progress(profile_id)

    # Missions assigned by the teacher ---------------------------------------------------

    @staticmethod
    def _done_path(profile_id: str, mission_id: str) -> str:
        return AdminClient.child_path(profile_id, f"missions/{quote(mission_id, safe='')}/done/")

    def cached_missions(self, profile_id: str) -> MissionList:
        return cached_missions(self.settings, profile_id)

    def _take_missions(self, profile_id: str, response: AdminResponse) -> MissionList | None:
        if not response.ok:
            return None
        try:
            listing = MissionList.model_validate(response.data)
        except ValidationError:
            LOG.warning("Ignored an invalid mission list from the administration")
            return None
        self.settings.save_assigned_missions(profile_id, listing.model_dump(mode="json"))
        return listing

    def fetch_missions(self, profile_id: str, on_missions: Callable[[MissionList], None]) -> None:
        """Load the missions for this child; keeps the copy on this PC for offline use."""

        def done(response: AdminResponse) -> None:
            listing = self._take_missions(profile_id, response)
            if listing is not None:
                on_missions(listing)

        self.client.request("GET", AdminClient.child_path(profile_id, "missions/"), on_done=done)

    def report_mission_done(
        self,
        profile_id: str,
        mission_id: str,
        on_missions: Callable[[MissionList], None] | None = None,
    ) -> None:
        """Remembered first, so a missing network connection only delays the report."""
        self.settings.add_pending_mission_report(profile_id, mission_id)

        def done(response: AdminResponse) -> None:
            if response.status == 0:
                return
            self.settings.clear_pending_mission_report(profile_id, mission_id)
            listing = self._take_missions(profile_id, response)
            if listing is not None and on_missions is not None:
                on_missions(listing)

        self.client.request("POST", self._done_path(profile_id, mission_id), on_done=done)


def cached_missions(settings: AppSettings, profile_id: str) -> MissionList:
    try:
        return MissionList.model_validate(settings.assigned_missions(profile_id))
    except ValidationError:
        return MissionList()
