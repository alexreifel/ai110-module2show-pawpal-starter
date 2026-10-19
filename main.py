"""CLI testing ground for the PawPal+ backend. Run: python main.py"""

from pawpal_system import Owner, Pet, Scheduler, Task


def show(title, tasks):
    """Print a heading and one line per task."""
    print(f"\n== {title} ==")
    for t in tasks:
        when = f"{t.preferred_time:%H:%M}" if t.preferred_time else "--:--"
        status = "done" if t.completed else f"due {t.due_date}"
        print(f"  {when}  {t.title:<18} {t.pet_name:<6} [{t.priority}] {t.frequency}, {status}")


def main():
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=7, notes="on thyroid meds")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order.
    mochi.add_task(Task("Evening walk", 25, "medium", "walk", preferred_time="18:30"))
    luna.add_task(Task("Clean litter box", 10, "medium"))
    mochi.add_task(Task("Morning walk", 30, "high", "walk", preferred_time="08:00"))
    luna.add_task(Task("Thyroid pill", 5, "high", "meds", preferred_time="08:00"))  # clashes with walk
    mochi.add_task(Task("Breakfast", 10, "high", "feeding", preferred_time="07:30"))
    mochi.add_task(Task("Flea treatment", 5, "high", "meds", preferred_time="08:15", frequency="once"))  # same-pet clash
    mochi.add_task(Task("Brushing", 45, "low", "grooming", frequency="weekly"))

    scheduler = Scheduler(owner)

    show("All tasks, sorted by time", scheduler.sort_by_time())
    show("Filter: Luna's tasks", scheduler.filter_tasks(pet_name="Luna"))

    # Completing tasks: Breakfast is daily (comes back tomorrow), Flea treatment is once (doesn't).
    breakfast = next(t for t in mochi.tasks if t.title == "Breakfast")
    scheduler.mark_task_complete(breakfast.id)
    show("Filter: completed", scheduler.filter_tasks(completed=True))
    show("Filter: Mochi, still open (note tomorrow's Breakfast)", scheduler.filter_tasks("Mochi", completed=False))

    plan = scheduler.build_plan()
    print()
    print(plan.summary())
    print()
    print(plan.explain())


if __name__ == "__main__":
    main()
