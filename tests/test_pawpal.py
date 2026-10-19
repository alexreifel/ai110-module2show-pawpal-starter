from datetime import date, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, ScheduledTask, Task


def make_scheduler():
    """Owner with two pets and tasks added out of time order."""
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Evening walk", 20, preferred_time="18:30"))
    luna.add_task(Task("Litter box", 10))
    mochi.add_task(Task("Breakfast", 10, preferred_time="07:30"))
    luna.add_task(Task("Pill", 5, preferred_time="08:00"))
    return Scheduler(owner)


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1


def test_sort_by_time_orders_clock_times_and_puts_untimed_last():
    titles = [t.title for t in make_scheduler().sort_by_time()]
    assert titles == ["Breakfast", "Pill", "Evening walk", "Litter box"]


def test_filter_tasks_by_pet_and_status():
    scheduler = make_scheduler()
    assert {t.title for t in scheduler.filter_tasks(pet_name="Luna")} == {"Litter box", "Pill"}

    pill = scheduler.filter_tasks(pet_name="Luna")[1]
    scheduler.mark_task_complete(pill.id)
    assert [t.title for t in scheduler.filter_tasks(completed=True)] == ["Pill"]


def test_completing_daily_task_creates_next_one_due_tomorrow():
    pet = Pet("Mochi", "dog")
    task = Task("Breakfast", 10, frequency="daily")
    pet.add_task(task)

    pet.complete_task(task.id)

    assert len(pet.tasks) == 2
    assert pet.tasks[-1].due_date == date.today() + timedelta(days=1)
    assert pet.tasks[-1].completed is False


def test_detect_conflicts_catches_non_neighboring_overlap():
    # A 08:00-09:00 overlaps both B and C, even though B sits between them.
    a = ScheduledTask(Task("A", 60, pet_name="Mochi"), time(8, 0), time(9, 0))
    b = ScheduledTask(Task("B", 10, pet_name="Luna"), time(8, 10), time(8, 20))
    c = ScheduledTask(Task("C", 10, pet_name="Mochi"), time(8, 30), time(8, 40))

    warnings = Scheduler(Owner("Jordan")).detect_conflicts([a, b, c])

    assert len(warnings) == 2
    assert any("A and C" in w and "same pet (Mochi)" in w for w in warnings)
    assert any("A and B" in w and "different pets" in w for w in warnings)


# --- Sorting --------------------------------------------------------------


def test_sort_by_time_is_chronological_regardless_of_insert_order():
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    for hhmm in ["21:00", "06:45", "12:00", "06:30", "09:15"]:
        pet.add_task(Task(f"Task at {hhmm}", 5, preferred_time=hhmm))

    times = [t.preferred_time for t in Scheduler(owner).sort_by_time()]

    assert times == sorted(times)
    assert f"{times[0]:%H:%M}" == "06:30"


def test_sort_by_time_with_no_tasks_returns_empty_list():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", "dog"))

    assert Scheduler(owner).sort_by_time() == []


# --- Recurrence -----------------------------------------------------------


def test_scheduler_mark_task_complete_creates_next_day_task():
    scheduler = make_scheduler()
    breakfast = next(t for t in scheduler.owner.get_all_tasks() if t.title == "Breakfast")

    scheduler.mark_task_complete(breakfast.id)

    copies = [t for t in scheduler.owner.get_all_tasks() if t.title == "Breakfast"]
    assert len(copies) == 2
    original, nxt = copies
    assert original.completed is True
    assert nxt.completed is False
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert nxt.id != original.id
    assert nxt.pet_name == "Mochi"


def test_weekly_task_comes_back_in_seven_days():
    task = Task("Brushing", 30, frequency="weekly")

    nxt = task.mark_complete()

    assert nxt.due_date == date.today() + timedelta(days=7)


def test_once_task_does_not_repeat():
    pet = Pet("Mochi", "dog")
    task = Task("Vet visit", 60, frequency="once")
    pet.add_task(task)

    pet.complete_task(task.id)

    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_overdue_daily_task_comes_back_tomorrow_not_still_overdue():
    task = Task("Breakfast", 10, frequency="daily", due_date=date.today() - timedelta(days=3))

    nxt = task.mark_complete()

    assert nxt.due_date == date.today() + timedelta(days=1)


def test_completed_task_and_tomorrows_copy_are_not_in_todays_plan():
    scheduler = make_scheduler()
    breakfast = next(t for t in scheduler.owner.get_all_tasks() if t.title == "Breakfast")
    scheduler.mark_task_complete(breakfast.id)

    planned = [i.task.title for i in scheduler.build_plan().scheduled]

    assert "Breakfast" not in planned


def test_mark_task_complete_unknown_id_raises():
    with pytest.raises(KeyError):
        make_scheduler().mark_task_complete(999_999)


# --- Conflict detection ---------------------------------------------------


def test_build_plan_flags_two_pets_at_exact_same_time():
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 30, preferred_time="08:00"))
    luna.add_task(Task("Pill", 5, preferred_time="08:00"))

    warnings = Scheduler(owner).build_plan().warnings

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "different pets" in warnings[0]
    assert "Mochi" in warnings[0] and "Luna" in warnings[0]


def test_build_plan_flags_same_pet_duplicate_time():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", 30, preferred_time="08:00"))
    mochi.add_task(Task("Flea treatment", 5, preferred_time="08:00"))

    warnings = Scheduler(owner).build_plan().warnings

    assert len(warnings) == 1
    assert "same pet (Mochi)" in warnings[0]


def test_back_to_back_tasks_are_not_a_conflict():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", 30, preferred_time="08:00"))
    mochi.add_task(Task("Breakfast", 10, preferred_time="08:30"))  # starts as walk ends

    assert Scheduler(owner).build_plan().warnings == []


def test_flexible_tasks_are_placed_around_pinned_tasks():
    owner = Owner("Jordan", day_start=time(8, 0))
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", 30, "high", preferred_time="08:00"))
    mochi.add_task(Task("Play", 20, "medium"))  # no preferred time

    plan = Scheduler(owner).build_plan()
    play = next(i for i in plan.scheduled if i.task.title == "Play")

    assert play.start_time == time(8, 30)
    assert plan.warnings == []


# --- Plans, budget and empty cases ---------------------------------------


def test_owner_with_no_pets_gets_empty_plan():
    plan = Scheduler(Owner("Jordan")).build_plan()

    assert plan.scheduled == []
    assert plan.skipped == []
    assert plan.warnings == []
    assert plan.total_minutes == 0


def test_pet_with_no_tasks_does_not_break_plan_for_other_pets():
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)  # Luna has no tasks
    mochi.add_task(Task("Walk", 30))

    plan = Scheduler(owner).build_plan()

    assert [i.task.title for i in plan.scheduled] == ["Walk"]


def test_budget_skips_long_task_but_still_fits_shorter_one():
    owner = Owner("Jordan", available_minutes=30)
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", 20, "high"))
    mochi.add_task(Task("Grooming", 45, "medium"))  # too long for what's left
    mochi.add_task(Task("Treat puzzle", 10, "low"))  # exactly fills the rest

    plan = Scheduler(owner).build_plan()

    assert [i.task.title for i in plan.scheduled] == ["Walk", "Treat puzzle"]
    assert [t.title for t, _ in plan.skipped] == ["Grooming"]
    assert plan.total_minutes == 30


def test_high_priority_wins_when_time_is_short():
    owner = Owner("Jordan", available_minutes=10)
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Play", 10, "low"))
    mochi.add_task(Task("Meds", 10, "high"))

    plan = Scheduler(owner).build_plan()

    assert [i.task.title for i in plan.scheduled] == ["Meds"]


# --- Input validation -----------------------------------------------------


def test_invalid_priority_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 30, "High")


def test_hhmm_string_is_converted_to_time():
    assert Task("Walk", 30, preferred_time="07:05").preferred_time == time(7, 5)


def test_zero_duration_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 0)


def test_task_running_past_day_end_is_flagged():
    owner = Owner("Jordan", day_end=time(21, 0))
    mochi = Pet("Mochi", "dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Late walk", 30, preferred_time="20:50"))

    warnings = Scheduler(owner).build_plan().warnings

    assert warnings == ["Late walk runs past day end (21:00)"]


# --- Pet and Owner bookkeeping --------------------------------------------


def test_pet_edit_get_and_remove_tasks():
    pet = Pet("Mochi", "dog")
    walk, meds = Task("Walk", 30), Task("Meds", 5)
    pet.add_task(walk)
    pet.add_task(meds)

    pet.edit_task(walk.id, duration_minutes=45)
    assert walk.duration_minutes == 45
    with pytest.raises(AttributeError):
        pet.edit_task(walk.id, not_a_field=1)

    meds.completed = True
    assert pet.get_tasks() == [walk]
    assert pet.get_tasks(include_completed=True) == [walk, meds]

    pet.remove_task(meds.id)
    assert pet.tasks == [walk]
    with pytest.raises(KeyError):
        pet.remove_task(meds.id)


def test_owner_remove_pet_and_set_availability():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))

    owner.remove_pet("Mochi")
    owner.set_availability(60, time(9, 0), time(17, 0))

    assert [p.name for p in owner.pets] == ["Luna"]
    assert (owner.available_minutes, owner.day_start, owner.day_end) == (60, time(9, 0), time(17, 0))


# --- Plan output ----------------------------------------------------------


def test_plan_summary_explain_and_rows():
    scheduler = make_scheduler()
    plan = scheduler.build_plan()

    assert "Today's Schedule" in plan.summary()
    assert "07:30–07:40  Breakfast (Mochi)" in plan.summary()
    assert "Breakfast: medium priority; at preferred time 07:30" in plan.explain()
    assert len(plan.to_rows()) == len(plan.scheduled)
    assert plan.to_rows()[0].keys() == {"time", "pet", "task", "priority", "why"}
    assert scheduler.owner.pets[0].tasks[0].to_dict()["title"] == "Evening walk"


def test_empty_plan_summary_says_nothing_scheduled():
    assert "Nothing scheduled." in Scheduler(Owner("Jordan")).build_plan().summary()
