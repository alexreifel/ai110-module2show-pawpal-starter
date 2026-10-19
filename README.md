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
3. **Filter** by adding tasks until the time budget runs out. Tasks that don't fit are skipped with a reason. The budget is the smaller of the owner's available minutes and their day window.
4. **Assign times.** Tasks with a preferred time are pinned there; the rest fill the earliest open gaps from the start of the day.
5. **Detect conflicts** such as overlapping slots or tasks running past the end of the day, and report them as warnings.

`main.py` is a command-line demo of this flow, and `tests/test_pawpal.py` holds the pytest tests.

## 🖥️ Sample Output

Output of `python main.py` (owner Jordan with 90 minutes available, two pets, six tasks):

```text
Today's Schedule (2026-10-19) — 75 min planned
  07:00–07:10  Clean litter box (Luna) [medium]
  07:10–07:30  Fetch in the yard (Mochi) [medium]
  07:30–07:40  Breakfast (Mochi) [high]
  08:00–08:05  Thyroid pill (Luna) [high]
  08:00–08:30  Morning walk (Mochi) [high]

Why this plan:
  - Clean litter box: medium priority; placed in next open slot
  - Fetch in the yard: medium priority; placed in next open slot
  - Breakfast: high priority; at preferred time 07:30
  - Thyroid pill: high priority; at preferred time 08:00
  - Morning walk: high priority; at preferred time 08:00
  - SKIPPED Brushing (Mochi): not enough time (45 min needed, 15 min left)
  ! Conflict: Thyroid pill (Luna) and Morning walk (Mochi) overlap at 08:00
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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
