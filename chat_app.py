"""Standalone conversational SQL query generator with a 3 follow-up limit."""

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

FOLLOWUP_LIMIT = 3

SYSTEM_PROMPT = """You are an expert PostgreSQL SQL query generator.

You help users write PostgreSQL queries against a single table called `Flights data`
with the following columns:

- "S.no" (row number / primary key)
- airline (text)
- flight (text, flight number/code)
- source_city (text)
- departure_time (text, e.g. Morning/Afternoon/Evening/Night)
- stops (text, e.g. zero/one/two_or_more)
- arrival_time (text, e.g. Morning/Afternoon/Evening/Night)
- destination_city (text)
- class (text, e.g. Economy/Business)
- duration (numeric, flight duration in hours)
- days_left (integer, days left until departure)
- price (numeric, ticket price)

Given the user's question, respond with a valid PostgreSQL query that answers it.
Use double-quoted identifiers for columns/tables that contain spaces or dots,
e.g. "Flights data" and "S.no". Only return the SQL query, optionally with a very
brief explanation, and prefer wrapping the SQL in a ```sql code block.
"""

st.set_page_config(
    page_title="SQL Chat (Follow-ups)",
    page_icon=":material/forum:",
    layout="wide",
)


def reset_session():
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.followup_count = 0


if "messages" not in st.session_state:
    reset_session()
if "followup_count" not in st.session_state:
    st.session_state.followup_count = 0


with st.sidebar:
    st.subheader("Session", anchor=False)
    st.metric("Follow-ups used", f"{st.session_state.followup_count} / {FOLLOWUP_LIMIT}")
    if st.button("Start New Session / Reset", icon=":material/refresh:", width="stretch"):
        reset_session()
        st.rerun()
    st.caption(
        "This session is limited to a fixed number of follow-up questions to keep "
        "token/context costs under control."
    )

st.markdown("# :material/forum: Conversational SQL Query Generator")

remaining = max(FOLLOWUP_LIMIT - st.session_state.followup_count, 0)
if remaining > 0:
    st.info(f"Follow-ups remaining: {remaining} of {FOLLOWUP_LIMIT}", icon=":material/info:")
else:
    st.warning(
        "Follow-up limit reached (3/3). To prevent excessive token consumption, this "
        "session can no longer accept new questions. Click **Start New Session / Reset** "
        "in the sidebar to begin again.",
        icon=":material/warning:",
    )

# ---- Render conversation history (skip the system prompt) ----------------
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---- Chat input ------------------------------------------------------------
limit_reached = st.session_state.followup_count >= FOLLOWUP_LIMIT
user_prompt = st.chat_input(
    "Ask a follow-up question about the Flights data table..."
    if not limit_reached
    else "Follow-up limit reached (3/3). Reset session to ask new questions.",
    disabled=limit_reached,
)

if user_prompt:
    st.session_state.followup_count += 1
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating SQL..."):
            try:
                client = OpenAI()
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages,
                )
                assistant_reply = response.choices[0].message.content
            except Exception as e:
                assistant_reply = f"Error generating response: {e}"
        st.markdown(assistant_reply)

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.rerun()
