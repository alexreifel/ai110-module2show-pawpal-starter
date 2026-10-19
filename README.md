# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

The backend lives in `pawpal_system.py` and is made of six dataclasses:

| Class | Role |
|---|---|
| `Task` | One care activity: title, duration, priority, optional preferred time, how often it repeats, due date, completed flag. Completing a daily or weekly task creates its next occurrence. |
| `Pet` | A pet's details plus its own list of tasks. Adds, edits, removes and completes tasks by id. |
| `Owner` | Holds the pets and the constraints (minutes available, day start and end). `get_all_tasks()` returns every pet's tasks in one list. |
| `Scheduler` | The "brain." Reads tasks only through `owner.get_all_tasks()`, so it plans across all pets at once. |
| `ScheduledTask` | A task placed at a start and end time, plus the reason it was placed there. |
| `DailyPlan` | The result: scheduled tasks, skipped tasks with reasons, and warnings. Can print a summary, explain itself, or turn into table rows. |

How a plan is built (`Scheduler.build_plan()`):

1. **Collect** every task from every pet that is due today and not completed.
2. **Sort** by priority (high first), then preferred time, then shortest first.
3. **Fit to budget** (`fit_to_budget`) by adding tasks until the time budget runs out. Tasks that don't fit are skipped with a reason. The budget is the smaller of the owner's available minutes and their day window.
4. **Assign times.** Tasks with a preferred time are pinned there; the rest fill the earliest open gaps from the start of the day.
5. **Detect conflicts** such as overlapping slots or tasks running past the end of the day, and report them as warnings.

`main.py` is a command-line demo of this flow, and `tests/test_pawpal.py` holds the pytest tests.

## 🖥️ Sample Output

Output of `python main.py` (owner Jordan with 90 minutes available, two pets, seven tasks added out of time order):

```text
== All tasks, sorted by time ==
  07:30  Breakfast          Mochi  [high] daily, due 2026-10-19
  08:00  Morning walk       Mochi  [high] daily, due 2026-10-19
  08:00  Thyroid pill       Luna   [high] daily, due 2026-10-19
  08:15  Flea treatment     Mochi  [high] once, due 2026-10-19
  18:30  Evening walk       Mochi  [medium] daily, due 2026-10-19
  --:--  Brushing           Mochi  [low] weekly, due 2026-10-19
  --:--  Clean litter box   Luna   [medium] daily, due 2026-10-19

== Filter: Luna's tasks ==
  --:--  Clean litter box   Luna   [medium] daily, due 2026-10-19
  08:00  Thyroid pill       Luna   [high] daily, due 2026-10-19

== Filter: completed ==
  07:30  Breakfast          Mochi  [high] daily, done

== Filter: Mochi, still open (note tomorrow's Breakfast) ==
  18:30  Evening walk       Mochi  [medium] daily, due 2026-10-19
  08:00  Morning walk       Mochi  [high] daily, due 2026-10-19
  08:15  Flea treatment     Mochi  [high] once, due 2026-10-19
  --:--  Brushing           Mochi  [low] weekly, due 2026-10-19
  07:30  Breakfast          Mochi  [high] daily, due 2026-10-20

Today's Schedule (2026-10-19) — 75 min planned
  07:00–07:10  Clean litter box (Luna) [medium]
  08:00–08:05  Thyroid pill (Luna) [high]
  08:00–08:30  Morning walk (Mochi) [high]
  08:15–08:20  Flea treatment (Mochi) [high]
  18:30–18:55  Evening walk (Mochi) [medium]

Why this plan:
  - Clean litter box: medium priority; placed in next open slot
  - Thyroid pill: high priority; at preferred time 08:00
  - Morning walk: high priority; at preferred time 08:00
  - Flea treatment: high priority; at preferred time 08:15
  - Evening walk: medium priority; at preferred time 18:30
  - SKIPPED Brushing (Mochi): not enough time (45 min needed, 15 min left)
  ! Conflict at 08:00: Thyroid pill and Morning walk overlap — different pets (Luna & Mochi)
  ! Conflict at 08:15: Morning walk and Flea treatment overlap — same pet (Mochi)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | In one line |
|---------|-----------|-------------|
| Sorting by time | `Scheduler.sort_by_time()` | Clock order by preferred time; untimed tasks last |
| Planning order | `Scheduler.sort_tasks()` | Priority, then preferred time, then shortest first |
| Filtering | `Scheduler.filter_tasks()` | By pet name and/or completion status, across all pets |
| Time budget | `Scheduler.fit_to_budget()` | Greedily keeps tasks until the minutes run out; skipped tasks get a reason |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on overlapping durations, labeled same pet or different pets |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Completing a daily or weekly task creates the next one automatically |

### Sorting — `Scheduler.sort_by_time()`

Returns every task across all pets (or a list you pass in) in clock order. It uses `sorted()` with a lambda key, `(t.preferred_time is None, t.preferred_time)`. `False` sorts before `True`, so timed tasks come first and tasks with no time go last. Times can be given as `"HH:MM"` strings and are converted to `time` objects. Zero-padded `"HH:MM"` strings would also sort correctly as plain text, but `time` objects make the scheduling math simpler.

`Scheduler.sort_tasks()` is a separate ordering used for *planning*: high priority first, then preferred time, then shorter tasks.

### Filtering — `Scheduler.filter_tasks(pet_name=None, completed=None)`

Reads from `Owner.get_all_tasks()`, so it works across every pet. Each argument is optional, and `None` means "don't filter on this":

- `filter_tasks(pet_name="Luna")` returns all of Luna's tasks.
- `filter_tasks(completed=False)` returns every open task.
- `filter_tasks("Mochi", completed=False)` returns Mochi's open tasks.

`Scheduler.fit_to_budget()` is the scheduling filter. It keeps tasks in priority order while they fit the owner's time budget, and skips the rest with a reason such as `not enough time (45 min needed, 15 min left)`.

### Conflict detection — `Scheduler.detect_conflicts()`

Checks **overlapping durations**, not just identical start times, so a 08:00–08:30 walk and an 08:15 flea treatment conflict. Slots are sorted by start time. Each slot is compared with the later slots until one starts after it ends; past that point nothing can overlap. That catches every overlapping pair, including ones that aren't next to each other. Each warning names the pets involved:

```text
! Conflict at 08:00: Thyroid pill and Morning walk overlap — different pets (Luna & Mochi)
! Conflict at 08:15: Morning walk and Flea treatment overlap — same pet (Mochi)
```

Conflicts are reported, not auto-fixed. Tasks with a preferred time stay where the owner put them. It also warns if a task runs past the owner's end of day.

### Recurring tasks — `Task.mark_complete()` / `Scheduler.mark_task_complete()`

`Scheduler.mark_task_complete(task_id)` finds which pet owns the task and calls `Pet.complete_task()`. That calls `Task.mark_complete()`:

- **daily** creates a new copy due `today + timedelta(days=1)`
- **weekly** creates a new copy due `today + timedelta(days=7)`
- **once** is just marked done, with no new copy

The new copy gets a fresh id. Because the next date counts from today, an overdue task comes back tomorrow rather than still overdue.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
