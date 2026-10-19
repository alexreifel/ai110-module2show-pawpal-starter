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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
- **The UML files:** the AI kept two identical UML files (`uml.mmd` and `uml_draft.mmd`). I questioned why, and we deleted the draft, because the grader expects `uml.mmd`.
- **A tradeoff I noticed:** in the output, medium-priority tasks get the earliest open slots, because high-priority tasks are pinned to their preferred times. I kept that behavior, but only after understanding why it happens.

**How I verified the result:**

- **The diagram:** a short script compared every class's attributes and methods in the UML against the code to make sure they matched.
- **The demo:** I ran `python main.py` and checked the schedule by hand: priorities in order, the skipped task's math (45 minutes needed, 15 left), and the overlap warning at 08:00.
- **Repeating tasks and validation:** checked separately. A completed daily task comes back due tomorrow with a new ID, and a bad priority like `"High"` is rejected.
- **Tests:** `pytest` runs the tests for task completion and adding tasks, and both pass.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
