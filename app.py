from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for the day based on time, priority, and preferred times.")

# Streamlit reruns this whole script on every click, so the Owner lives in
# session_state ("the vault") and is only created the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Owner -----------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
col1, col2, col3 = st.columns(3)
with col1:
    minutes = st.number_input("Minutes available today", 10, 24 * 60, owner.available_minutes, step=10)
with col2:
    start = st.time_input("Day starts", owner.day_start)
with col3:
    end = st.time_input("Day ends", owner.day_end)
owner.set_availability(int(minutes), start, end)

st.divider()

# --- Pets ------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        elif any(p.name == pet_name.strip() for p in owner.pets):
            st.error(f"You already have a pet named {pet_name.strip()}.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species, age=int(age)))
            st.success(f"Added {pet_name.strip()}!")

if owner.pets:
    st.table([{"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks -----------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("For which pet?", [p.name for p in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            title = st.text_input("Task", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col1, col2, col3 = st.columns(3)
        with col1:
            frequency = st.selectbox("Repeats", ["daily", "weekly", "once"])
        with col2:
            has_time = st.checkbox("Has a preferred time")
        with col3:
            preferred = st.time_input("Preferred time", time(8, 0))
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == pet_choice)
            pet.add_task(
                Task(
                    title.strip() or "Untitled task",
                    int(duration),
                    priority,
                    preferred_time=preferred if has_time else None,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{title}' for {pet_choice}.")

    # Mark complete sits above the task list so the list shows the change right away.
    open_tasks = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if open_tasks:
        col1, col2 = st.columns([3, 1])
        with col1:
            to_complete = st.selectbox(
                "Mark a task complete",
                open_tasks,
                format_func=lambda t: f"{t.pet_name} — {t.title} "
                f"({t.preferred_time:%H:%M}, due {t.due_date})" if t.preferred_time
                else f"{t.pet_name} — {t.title} (any time, due {t.due_date})",
            )
        with col2:
            st.write("")  # aligns the button with the selectbox
            if st.button("Mark complete"):
                scheduler.mark_task_complete(to_complete.id)
                if to_complete.frequency == "once":
                    st.success(f"Done! '{to_complete.title}' is complete.")
                else:
                    nxt = next(p for p in owner.pets if p.name == to_complete.pet_name).tasks[-1]
                    st.success(f"Done! Next '{nxt.title}' is due {nxt.due_date:%a %b %d}.")

    st.markdown("**Task list** (sorted by time)")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status = st.radio("Status", ["Open", "Done", "All"], horizontal=True)
    filtered = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"Open": False, "Done": True, "All": None}[status],
    )
    if filtered:
        st.table(
            [
                {
                    "time": f"{t.preferred_time:%H:%M}" if t.preferred_time else "any",
                    "pet": t.pet_name,
                    "task": t.title,
                    "minutes": t.duration_minutes,
                    "priority": t.priority,
                    "repeats": t.frequency,
                    "due": t.due_date.isoformat(),
                    "status": "✅ done" if t.completed else "open",
                }
                for t in scheduler.sort_by_time(filtered)
            ]
        )
    else:
        st.info("No tasks match this filter.")

st.divider()

# --- Schedule --------------------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    plan = scheduler.build_plan()
    if not plan.scheduled:
        st.info("Nothing to schedule today — add some tasks first.")
    else:
        st.success(
            f"Planned {len(plan.scheduled)} tasks — "
            f"{plan.total_minutes} of {owner.available_minutes} minutes."
        )
        # Conflicts go first, as warnings (not errors): some overlaps are fine,
        # so tell the owner what clashes and what they can do about it.
        for warning in plan.warnings:
            tip = (
                "Move one of these tasks to a different time above, or ignore this "
                "if two people can handle them at once."
                if warning.startswith("Conflict")
                else "Shorten the task or move it earlier, or extend your day end time."
            )
            st.warning(f"⚠️ {warning}  \n**Tip:** {tip}")
        st.table(plan.to_rows())
    for task, reason in plan.skipped:
        st.info(f"Skipped **{task.title}** ({task.pet_name}): {reason}")
    with st.expander("Why this plan?"):
        st.text(plan.explain())
