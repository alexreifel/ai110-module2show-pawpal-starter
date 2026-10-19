from datetime import date, time, timedelta

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
