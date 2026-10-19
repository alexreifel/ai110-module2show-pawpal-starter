"""PawPal+ backend: data classes and scheduling logic."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from typing import Optional

_task_ids = itertools.count(1)

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}  # "once" does not recur


def _to_minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    """Convert minutes since midnight back to a time (capped at 23:59)."""
    minutes = min(minutes, 23 * 60 + 59)
    return time(minutes // 60, minutes % 60)


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "other"
    preferred_time: time | str | None = None  # "HH:MM" strings are converted to time
    frequency: str = "daily"  # "daily" | "weekly" | "once"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task
    due_date: date = field(default_factory=date.today)
    id: int = field(default_factory=lambda: next(_task_ids))

    def __post_init__(self):
        """Validate priority and duration, and accept "HH:MM" strings for preferred_time."""
        if isinstance(self.preferred_time, str):
            self.preferred_time = time.fromisoformat(self.preferred_time)
        if self.priority not in PRIORITY_SCORES:
            raise ValueError(f"priority must be one of {list(PRIORITY_SCORES)}, got {self.priority!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> Optional[Task]:
        """Mark this task done; return a copy due on the next date if it recurs.

        The next date counts from today (or the due date, if that's later), so
        an overdue daily task comes back tomorrow instead of still overdue.
        """
        self.completed = True
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        base = max(self.due_date, date.today())
        return replace(
            self,
            completed=False,
            due_date=base + timedelta(days=days),
            id=next(_task_ids),
        )

    def priority_score(self) -> int:
        """Return a numeric priority (higher = more important) for sorting."""
        return PRIORITY_SCORES[self.priority]

    def is_due_today(self, day: date) -> bool:
        """Return True if not completed and due_date is on or before `day`."""
        return not self.completed and self.due_date <= day

    def to_dict(self) -> dict:
        """Return a dict suitable for display in st.table."""
        return {
            "id": self.id,
            "pet": self.pet_name,
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "preferred_time": self.preferred_time.strftime("%H:%M") if isinstance(self.preferred_time, time) else "",
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
        }


@dataclass
class Pet:
    """An animal being cared for, with its own task list."""

    name: str
    species: str
    age: Optional[int] = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def _find(self, task_id: int) -> Task:
        """Return this pet's task with the given id, or raise KeyError."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"{self.name} has no task with id {task_id}")

    def add_task(self, task: Task) -> None:
        """Add a task and stamp it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks.remove(self._find(task_id))

    def edit_task(self, task_id: int, **changes) -> None:
        """Update fields on the task with the given id (e.g. duration_minutes=15)."""
        task = self._find(task_id)
        for key, value in changes.items():
            if not hasattr(task, key):
                raise AttributeError(f"Task has no field {key!r}")
            setattr(task, key, value)

    def complete_task(self, task_id: int) -> None:
        """Mark a task complete and add its next occurrence (if any) to this pet."""
        next_task = self._find(task_id).mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)

    def get_tasks(self, include_completed: bool = False) -> list[Task]:
        """Return this pet's tasks, hiding completed ones unless asked."""
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]


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
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove every pet with the given name."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def set_availability(self, minutes: int, start: time, end: time) -> None:
        """Update the daily time budget and the start/end window."""
        self.available_minutes = minutes
        self.day_start = start
        self.day_end = end


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
        lines = [f"Today's Schedule ({self.date.isoformat()}) — {self.total_minutes} min planned"]
        for item in self.scheduled:
            t = item.task
            lines.append(
                f"  {item.start_time:%H:%M}–{item.end_time:%H:%M}  "
                f"{t.title} ({t.pet_name}) [{t.priority}]"
            )
        if not self.scheduled:
            lines.append("  Nothing scheduled.")
        return "\n".join(lines)

    def explain(self) -> str:
        """Explain why each task was scheduled or skipped."""
        lines = ["Why this plan:"]
        for item in self.scheduled:
            lines.append(f"  - {item.task.title}: {item.reason}")
        for task, reason in self.skipped:
            lines.append(f"  - SKIPPED {task.title} ({task.pet_name}): {reason}")
        for warning in self.warnings:
            lines.append(f"  ! {warning}")
        return "\n".join(lines)

    def to_rows(self) -> list[dict]:
        """Return rows suitable for st.table."""
        return [
            {
                "time": f"{i.start_time:%H:%M}–{i.end_time:%H:%M}",
                "pet": i.task.pet_name,
                "task": i.task.title,
                "priority": i.task.priority,
                "why": i.reason,
            }
            for i in self.scheduled
        ]


@dataclass
class Scheduler:
    """Builds a DailyPlan from an Owner's pets, tasks, and constraints."""

    owner: Owner

    def collect_tasks(self, day: Optional[date] = None) -> list[Task]:
        """Return tasks across all of the owner's pets that are due on `day`."""
        day = day or date.today()
        return [t for t in self.owner.get_all_tasks() if t.is_due_today(day)]

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order by priority desc, then preferred time, then shorter duration."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_score(), t.preferred_time or time.max, t.duration_minutes),
        )

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks in clock order by preferred_time; untimed tasks go last.

        The key is a tuple: (has no time?, the time). False sorts before True, so
        timed tasks come first. If times were stored as zero-padded "HH:MM"
        strings, `key=lambda t: t.time_str` would also work, since "07:30" < "08:00"
        compares correctly as text.

        Args:
            tasks: tasks to sort; defaults to every task across the owner's pets.
        """
        tasks = self.owner.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.preferred_time is None, t.preferred_time or time.min))

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return the owner's tasks (across all pets) that match every filter given.

        Args:
            pet_name: only tasks for this pet; None means any pet.
            completed: True for done tasks, False for open ones; None means either.

        Returns:
            Matching tasks in the order they were added.
        """
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def mark_task_complete(self, task_id: int) -> None:
        """Mark a task complete without needing to know which pet owns it.

        Finds the owning pet and calls Pet.complete_task, so a daily or weekly
        task gets a new copy due today + 1 or + 7 days; a "once" task doesn't.

        Raises:
            KeyError: if no pet has a task with this id.
        """
        for pet in self.owner.pets:
            if any(t.id == task_id for t in pet.tasks):
                pet.complete_task(task_id)
                return
        raise KeyError(f"No task with id {task_id}")

    def fit_to_budget(
        self, tasks: list[Task], minutes: int
    ) -> tuple[list[Task], list[tuple[Task, str]]]:
        """Greedily keep tasks, in the order given, while they fit within `minutes`.

        A task that doesn't fit is skipped with a reason, and the loop keeps going
        so a shorter task later in the list can still use the leftover time.

        Returns:
            (kept tasks, list of (skipped task, reason)).
        """
        kept, skipped, used = [], [], 0
        for task in tasks:
            if used + task.duration_minutes <= minutes:
                kept.append(task)
                used += task.duration_minutes
            else:
                skipped.append(
                    (task, f"not enough time ({task.duration_minutes} min needed, {minutes - used} min left)")
                )
        return kept, skipped

    def assign_times(self, tasks: list[Task]) -> list[ScheduledTask]:
        """Give each task a start and end time, returned in clock order.

        1. Tasks with a preferred_time are pinned exactly there (even if two
           pinned tasks overlap — detect_conflicts reports that).
        2. The rest are placed one after another from owner.day_start, in the
           order given (priority order from build_plan). Each one starts at the
           cursor and, walking the pinned slots in time order, jumps to the end
           of any pinned slot it would overlap. One pass is enough because the
           pinned slots are sorted.

        Args:
            tasks: the tasks to place (already sorted and fitted to the budget).

        Returns:
            A ScheduledTask per task, sorted by start time, each with a reason.
        """
        slots: list[tuple[int, int, Task, str]] = []
        for t in tasks:
            if isinstance(t.preferred_time, time):
                start = _to_minutes(t.preferred_time)
                slots.append((start, start + t.duration_minutes, t,
                              f"{t.priority} priority; at preferred time {t.preferred_time:%H:%M}"))

        pinned = sorted(slots, key=lambda s: s[0])  # by start time
        cursor = _to_minutes(self.owner.day_start)
        for t in tasks:
            if isinstance(t.preferred_time, time):
                continue
            start = cursor
            for s, e, _, _ in pinned:  # skip past any pinned slot this task would overlap
                if start < e and s < start + t.duration_minutes:
                    start = e
            slots.append((start, start + t.duration_minutes, t,
                          f"{t.priority} priority; placed in next open slot"))
            cursor = start + t.duration_minutes

        slots.sort(key=lambda s: s[0])
        return [ScheduledTask(t, _to_time(s), _to_time(e), reason) for s, e, t, reason in slots]

    def detect_conflicts(self, items: list[ScheduledTask]) -> list[str]:
        """Return a warning for every pair of overlapping slots and any slot past day_end.

        Checks overlapping durations, not just identical start times: 08:00–08:30
        and 08:15–08:20 count as a conflict. Slots are sorted by start, and each
        one is compared with the later slots until one starts after it ends.
        Warnings say whether the clash is for the same pet or different pets.
        Conflicts are only reported, never auto-fixed.
        """
        warnings = []
        ordered = sorted(items, key=lambda i: i.start_time)
        for i, a in enumerate(ordered):
            # Compare a with every later slot until one starts after a ends;
            # since the list is sorted by start, nothing after that can overlap a.
            for b in ordered[i + 1:]:
                if b.start_time >= a.end_time:
                    break
                if a.task.pet_name == b.task.pet_name:
                    who = f"same pet ({a.task.pet_name})"
                else:
                    who = f"different pets ({a.task.pet_name} & {b.task.pet_name})"
                warnings.append(
                    f"Conflict at {b.start_time:%H:%M}: {a.task.title} and {b.task.title} overlap — {who}"
                )
        for i in ordered:
            if i.end_time > self.owner.day_end:
                warnings.append(f"{i.task.title} runs past day end ({self.owner.day_end:%H:%M})")
        return warnings

    def build_plan(self, day: Optional[date] = None) -> DailyPlan:
        """Run collect → sort → filter → assign → detect and return a DailyPlan."""
        day = day or date.today()
        window = _to_minutes(self.owner.day_end) - _to_minutes(self.owner.day_start)
        budget = min(self.owner.available_minutes, window)

        tasks = self.sort_tasks(self.collect_tasks(day))
        kept, skipped = self.fit_to_budget(tasks, budget)
        scheduled = self.assign_times(kept)
        return DailyPlan(
            date=day,
            scheduled=scheduled,
            skipped=skipped,
            total_minutes=sum(t.duration_minutes for t in kept),
            warnings=self.detect_conflicts(scheduled),
        )
