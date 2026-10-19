# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML has six classes, split into three groups: data objects (Owner, Pet, Task), the scheduling logic (Scheduler), and the output (ScheduledTask, DailyPlan). I kept the scheduling logic in its own class, separate from the data, so it's easy to unit test without touching the UI. All six are Python dataclasses to keep the code short.

- **Owner**: the person doing the care. Holds the constraints: how many minutes are available today, the day's start and end times, and preferences. Owns a list of pets and can add or remove pets and gather every task across all of them.
- **Pet**: an animal (name, species, age, notes) that owns its own list of care tasks. Responsible for adding, removing, editing and listing its tasks.
- **Task**: one care activity, such as a walk, feeding or meds. Holds title, category, duration, priority (low/medium/high), an optional preferred time, how often it repeats (daily/weekly/once) and whether it's completed. It can turn its priority into a number for sorting, say whether it's due on a given day, and mark itself complete.
- **Scheduler**: the "brain." Given an Owner, it runs a pipeline: collect today's tasks → sort them (priority, then preferred time, then shorter duration) → drop tasks that don't fit the time budget → give each kept task a time slot → flag overlaps → return a DailyPlan.
- **ScheduledTask**: a Task placed at a specific start and end time, along with the reason it was placed there.
- **DailyPlan**: the result for one day: scheduled tasks, skipped tasks with reasons, total minutes, and warnings. It can summarize and explain itself, and turn itself into table rows for the Streamlit UI.

Relationships: an Owner has many Pets, a Pet has many Tasks, the Scheduler reads from the Owner and creates a DailyPlan, and a DailyPlan contains ScheduledTasks that each wrap one Task.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. The six classes stayed the same, but how they connect changed in a few important ways. The before and after diagrams are `diagrams/uml.mmd` and `diagrams/uml_final.mmd`.

- **Tasks got an `id` and a `due_date`.** The first design found tasks by title, which breaks as soon as a pet has two tasks with the same name. It also had no way to say *when* a repeating task was due. A simple id counter and a `due_date` field fixed both problems, and they're what make recurrence work.
- **Completing a task moved to the Pet, and then to the Scheduler.** Originally `Task.mark_complete()` returned the next occurrence, but a Task doesn't know which pet owns it, so the new task had nowhere to go. I added `Pet.complete_task()` to add it to the right list. Later I added `Scheduler.mark_task_complete()` so the UI can complete any task without knowing its pet first.
- **I renamed `filter_tasks` to `fit_to_budget`.** The original "filter" method really filtered by the time budget. When I needed a real filter by pet or status, I gave that one the name `filter_tasks` and renamed the budget method to say what it actually does.
- **The Scheduler gained `sort_by_time()`** for browsing tasks in clock order, separate from `sort_tasks()`, which orders them for planning (priority first).
- **`Scheduler` became a dataclass** like the others, and `assign_times()` was simplified to a single pass over the time slots (see 3b).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers four constraints:

1. **Time budget:** the owner's available minutes, capped by the length of their day (start to end).
2. **Priority:** high, medium or low.
3. **Preferred time:** an optional exact time for a task, such as meds at 08:00.
4. **Due date and status:** only tasks that are due today and not yet done are planned.

Priority decides **what** gets in, and preferred time decides **when** it happens. Priority matters most because the worst failure for a pet owner is that something important, like meds or feeding, gets dropped for something optional, like brushing. So tasks are sorted by priority before the budget is applied, and low-priority tasks are the first to be skipped. Preferred time comes second: it never decides whether a task makes the cut, only where it goes. Owner `preferences` are stored, but the scheduler doesn't use them yet. I chose to leave them out rather than guess at rules.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**The tradeoff: conflicts are detected but not fixed.** If a task has a preferred time, the scheduler pins it exactly there, even when it overlaps another pinned task. `detect_conflicts()` checks for overlapping durations, not just identical start times, so a 08:00–08:30 walk and an 08:15 flea treatment are flagged. But it only reports the conflict as a warning. It never moves either task.

This is reasonable for a pet owner for three reasons:

- **The owner knows things the scheduler doesn't.** Some "conflicts" are fine in real life: a cat's pill and a dog's walk at 08:00 might be handled by two people, or the pill takes 30 seconds before heading out.
- **Moving tasks automatically could do harm.** Meds are often time-sensitive. Quietly pushing a pill from 08:00 to 08:30 is worse than showing a warning and letting the owner decide.
- **It keeps the algorithm simple and the plan predictable.** A task with a preferred time always shows up at that time, and the warning explains any problem.

The cost is that the plan the app shows can be impossible as written. The owner has to read the warnings and adjust things themselves.

**How that shows up in the UI:** because conflicts are left for the owner to resolve, the app has to make them easy to spot. In Streamlit, each conflict is shown *above* the schedule table as a yellow `st.warning`, not a red error, since an overlap isn't necessarily wrong. Each warning names both tasks, both pets and the time, plus a tip: move one task, or ignore it if two people can help.

A second, smaller tradeoff: `fit_to_budget()` is **greedy**. It keeps tasks in priority order until the time runs out, rather than searching for the combination that fills the time best. Sometimes that leaves a few minutes unused. In exchange, it's easy to explain: higher priority always wins.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code (an AI coding assistant) through most of the design and build:

- **Design brainstorming:** it proposed the six classes with their attributes and methods, and turned them into the Mermaid UML diagram.
- **Turning the design into code:** it wrote the class stubs to match the UML, then the full implementation, `main.py`, and the first two pytest tests.
- **Design review:** I gave it the skeleton and asked whether it noticed missing relationships or likely logic bottlenecks before any logic was written.

The most helpful prompts were narrow and specific. "Brainstorm the objects, their attributes and methods" gave a clear starting point. "Look at my skeleton and find missing relationships or bottlenecks" caught real problems early, while everything was still a stub and cheap to change. Asking it to explain things, like "why is there both uml and uml_draft?", was also useful, because it made the AI justify what it had done instead of me just accepting it.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**What it suggested, and what I accepted or rejected:**

- **The skeleton review:** the AI listed about eight issues.
  - Tasks were tied to their pet only by a name string.
  - Tasks had no ID, so two tasks with the same title couldn't be told apart.
  - A completed repeating task had no way to add its next occurrence back to the pet.
  - Repeating tasks had no date to work from.
  - Owner preferences were never used.
  - The time budget was defined in two places.
  - Python's `time` objects can't have minutes added to them.
  - Overlapping time slots were only reported, never resolved.
- **What I accepted:** I didn't take all of it as-is. I told it to fix things without overcomplicating them. So it made only the minimal fixes: an auto-generated task `id`, a `due_date` field, and a `Pet.complete_task()` method.
- **What I set aside:** heavier ideas, like a priority Enum or a system for owner preferences. Priority is checked with a simple validation instead.
- **The UML files:** early on, the AI kept two identical UML files (`uml.mmd` and `uml_draft.mmd`). I questioned why, and we deleted the duplicate. At the end, I chose to restore `uml.mmd` to the original Phase 1 draft and keep the final version in `uml_final.mmd`, so the design change can be seen side by side.
- **Coverage:** while writing the testing docs, the AI removed the `pytest --cov` command from the README because `pytest-cov` wasn't installed. I pushed back. I wanted coverage, not less documentation. So we installed `pytest-cov`, added it to `requirements.txt`, and used it to raise coverage from 83% to 99%.
- **A tradeoff I noticed:** in the output, medium-priority tasks get the earliest open slots, because high-priority tasks are pinned to their preferred times. I kept that behavior, but only after understanding why it happens.

**Readable vs. "Pythonic":** I asked the AI how `Scheduler.assign_times()` could be simplified for readability or performance. It offered two versions:

- **A loop:** replace the nested `while moved:` loop with a single pass over the pinned time slots, sorted by start time.
- **A one-liner:** do the same thing with `functools.reduce` and a lambda.

I kept the plain loop. The `reduce` version is shorter, but you have to decode the lambda to see what it does, and it's no faster. Before swapping in the new loop, I had it compared against the old code on 200,000 random inputs, and the results were identical every time. The demo output didn't change either.

**How I verified the result:**

- **The diagram:** a short script compared every class's attributes and methods in the UML against the code to make sure they matched.
- **The demo:** I ran `python main.py` and checked the schedule by hand: priorities in order, the skipped task's math (45 minutes needed, 15 left), and the overlap warning at 08:00.
- **Repeating tasks and validation:** checked separately. A completed daily task comes back due tomorrow with a new ID, and a bad priority like `"High"` is rejected.
- **Tests:** the suite grew to 30 pytest tests with 99% coverage (see section 4).
- **The UI:** I checked the full app flow with Streamlit's test runner: adding pets and tasks, filtering, generating the schedule (where the conflict warning appears), and marking a task complete.
- **The final UML:** it was checked against the code with the same comparison script, and run through Mermaid's real parser to make sure it renders.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The suite has 30 tests in `tests/test_pawpal.py` and covers 99% of `pawpal_system.py`:

- **Sorting:** tasks added out of order come back in clock order, and tasks with no time go last.
- **Recurrence:** a completed daily task creates a new one due tomorrow, with a new id and the same pet; weekly means +7 days; "once" doesn't repeat; an overdue task comes back tomorrow; and none of these leak into today's plan.
- **Conflict detection:**
  - exact same-time clashes, for the same pet and for different pets
  - overlaps between tasks that aren't next to each other
  - back-to-back tasks, which must *not* be flagged
- **Planning:**
  - flexible tasks are placed around pinned ones
  - high priority wins when time is short
  - a task that's too long is skipped while a shorter one still fits
  - empty owners and empty pets don't crash
- **Bookkeeping and validation:**
  - editing, removing and filtering tasks
  - plan output (summary, explanation, table rows)
  - bad priorities, zero durations and unknown ids

These tests matter because a scheduler can look right in a demo but still be wrong at the edges. The back-to-back test protects against an off-by-one in the overlap check. The non-neighboring overlap test caught a real bug: my first conflict check only compared tasks next to each other. The recurrence tests pin down the date math, so a daily task can't silently stay overdue.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**4 out of 5.** Every scheduling feature is tested, including the edge cases most likely to break, and all 30 tests pass. What keeps it from 5:

- **The UI has no automated tests.** I only smoke-tested it with Streamlit's test runner.
- **The tests use the real current date.** Next I'd pass a fixed date into `build_plan()` and test month-end, year-end and leap days for recurring tasks.
- **Tasks near midnight are untested.** For example, a task at 23:50 that runs past 24:00.
- **Owner preferences aren't used yet,** so there's nothing to test there.
- **Conflicts aren't auto-resolved.** I'd want tests for a future "suggest a new time" feature.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The **CLI-first workflow**. Building and checking the logic in `main.py` and pytest before touching Streamlit meant that by the time I wired up the UI, the logic was already trusted. The UI work was just a matter of calling methods that already worked. I'm also happy with how the conflict detection turned out: it catches real overlaps, says whether the clash is the same pet or different pets, and has a test that caught a real bug in my first version.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Actually use owner preferences.** For example, "walks in the morning" or "no tasks after 20:00" as rules the scheduler applies.
- **Suggest fixes for conflicts.** When two tasks clash, offer the next free time instead of only warning.
- **Make dates testable and save data.** Pass `today` into the scheduler instead of calling `date.today()` inside it. Then save the owner's data, for example to a JSON file, so it survives closing the browser tab, since `st.session_state` doesn't.
- **Edit and delete tasks in the UI.** The backend already supports it, but the app only exposes adding and completing.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

AI makes building fast, but **I'm still responsible for scope and correctness**. The AI's first instinct was often to do more: more fixes, extra files, heavier abstractions. Its suggestions were usually *reasonable*, but saying "don't overcomplicate it" kept the design small enough that I can explain every part of it. And the AI didn't make the code trustworthy just by writing it. The tests, the coverage report, the UML-vs-code check and running the real app did. The most valuable habit was asking the AI *why*, and then making it prove the answer with something I could run.
