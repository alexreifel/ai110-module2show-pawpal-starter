"""PawPal+ backend: data classes and scheduling logic.

Class stubs only — logic will be implemented incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "other"
    preferred_time: Optional[time] = None
    frequency: str = "daily"  # "daily" | "weekly" | "once"
    completed: bool = False
    pet_name: str = ""

    def mark_complete(self) -> Optional[Task]:
        """Mark this task done; return the next occurrence if it recurs."""
        raise NotImplementedError

    def priority_score(self) -> int:
        """Return a numeric priority (higher = more important) for sorting."""
        raise NotImplementedError

    def is_due_today(self, day: date) -> bool:
        """Return True if this task should be considered for `day`."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Return a dict suitable for display in st.table."""
        raise NotImplementedError


@dataclass
class Pet:
    """An animal being cared for, with its own task list."""

    name: str
    species: str
    age: Optional[int] = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def remove_task(self, title: str) -> None:
        raise NotImplementedError

    def edit_task(self, title: str, **changes) -> None:
        raise NotImplementedError

    def get_tasks(self, include_completed: bool = False) -> list[Task]:
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner: holds pets, time budget, and preferences."""

    name: str
    available_minutes: int = 120
    day_start: time = time(7, 0)
    day_end: time = time(21, 0)
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def remove_pet(self, name: str) -> None:
        raise NotImplementedError

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks across all pets."""
        raise NotImplementedError

    def set_availability(self, minutes: int, start: time, end: time) -> None:
        raise NotImplementedError


@dataclass
class ScheduledTask:
    """A task placed at a specific time slot in the plan."""

    task: Task
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class DailyPlan:
    """The scheduler's output for one day."""

    date: date
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)
    total_minutes: int = 0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Short human-readable overview of the plan."""
        raise NotImplementedError

    def explain(self) -> str:
        """Explain why each task was scheduled or skipped."""
        raise NotImplementedError

    def to_rows(self) -> list[dict]:
        """Return rows suitable for st.table."""
        raise NotImplementedError


@dataclass
class Scheduler:
    """Builds a DailyPlan from an Owner's pets, tasks, and constraints."""

    owner: Owner

    def collect_tasks(self, day: Optional[date] = None) -> list[Task]:  # defaults to today
        """Return tasks that are due on `day` and not yet completed."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order by priority desc, then preferred time, then shorter duration."""
        raise NotImplementedError

    def filter_tasks(
        self, tasks: list[Task], minutes: int
    ) -> tuple[list[Task], list[tuple[Task, str]]]:
        """Greedily keep tasks that fit within `minutes`; return (kept, skipped)."""
        raise NotImplementedError

    def assign_times(self, tasks: list[Task]) -> list[ScheduledTask]:
        """Lay tasks out from owner.day_start, honoring preferred_time."""
        raise NotImplementedError

    def detect_conflicts(self, items: list[ScheduledTask]) -> list[str]:
        """Return warnings for overlapping time slots."""
        raise NotImplementedError

    def build_plan(self, day: Optional[date] = None) -> DailyPlan:
        """Run collect → sort → filter → assign → detect and return a DailyPlan."""
        raise NotImplementedError
