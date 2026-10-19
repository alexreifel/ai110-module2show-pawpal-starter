"""CLI testing ground for the PawPal+ backend. Run: python main.py"""

from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def main():
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=7, notes="on thyroid meds")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", "walk", preferred_time=time(8, 0)))
    mochi.add_task(Task("Breakfast", 10, "high", "feeding", preferred_time=time(7, 30)))
    mochi.add_task(Task("Fetch in the yard", 20, "medium", "enrichment"))
    mochi.add_task(Task("Brushing", 45, "low", "grooming", frequency="weekly"))
    luna.add_task(Task("Thyroid pill", 5, "high", "meds", preferred_time=time(8, 0)))
    luna.add_task(Task("Clean litter box", 10, "medium", "other"))

    plan = Scheduler(owner).build_plan()
    print(plan.summary())
    print()
    print(plan.explain())


if __name__ == "__main__":
    main()
