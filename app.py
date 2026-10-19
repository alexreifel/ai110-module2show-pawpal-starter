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

    tasks = owner.get_all_tasks()
    if tasks:
        st.table([t.to_dict() for t in tasks])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule --------------------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    plan = Scheduler(owner).build_plan()
    if plan.scheduled:
        st.write(f"**{plan.total_minutes} of {owner.available_minutes} minutes planned**")
        st.table(plan.to_rows())
    else:
        st.info("Nothing to schedule — add some tasks first.")
    for task, reason in plan.skipped:
        st.warning(f"Skipped **{task.title}** ({task.pet_name}): {reason}")
    for warning in plan.warnings:
        st.error(warning)
    with st.expander("Why this plan?"):
        st.text(plan.explain())
