import time

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from mydb import execute_query, get_schema, get_tables

load_dotenv()

st.set_page_config(
    page_title="SQL Query Generator",
    page_icon=":material/database:",
    layout="wide",
)

# Custom CSS (explicitly requested): pinned sidebar, hero banner, card shadows,
# button/chip polish. Colors, fonts and radii themselves live in
# .streamlit/config.toml so they survive Streamlit upgrades; this layer only
# adds the visual flourishes config.toml can't express.
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        overflow-y: auto;
        z-index: 999;
    }
    [data-testid="stSidebar"] > div:first-child {
        position: sticky;
        top: 0;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    div[class*="st-key-hero_box"] {
        padding: 1.75rem 2rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);
        margin-bottom: 1.5rem;
    }
    div[class*="st-key-hero_box"] * {
        color: #ffffff !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
        transition: box-shadow 0.2s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.10);
    }

    .stButton button {
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(16, 24, 40, 0.12);
    }

    div[class*="st-key-ex_"] button {
        border-radius: 999px;
        font-size: 0.85rem;
        padding: 0.25rem 0.9rem;
    }

    pre, .stCodeBlock {
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

EXAMPLE_QUESTIONS = [
    "What were total sales last month?",
    "Show the 10 most recent orders",
    "Which customer placed the most orders?",
    "What is the average order value this year?",
]


@st.cache_resource
def get_openai_client():
    return OpenAI()


@st.cache_data(ttl=3600)
def load_available_tables():
    return get_tables()


@st.cache_data(ttl=3600)
def load_database_schema(table_name="order"):
    schema_df = get_schema(table_name)
    schema_text = "Table: " + table_name + "\n\n"
    for _, row in schema_df.iterrows():
        schema_text += f"{row['column_name']}: {row['data_type']}\n"
    return schema_text


def clean_sql_response(response_str: str) -> str:
    cleaned = response_str.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0]
    return cleaned.strip()


def start_new_question(question: str):
    """Reset downstream state and queue `question` for generation."""
    st.session_state.current_question = question
    st.session_state.generated_query = None
    st.session_state.query_results = None
    st.session_state.execution_status = None
    st.session_state.should_show_query = True
    st.session_state.exec_elapsed = None
    if question not in st.session_state.questions:
        st.session_state.questions.append(question)


# ---- Session state -------------------------------------------------------
for key, default in {
    "questions": [],
    "generated_query": None,
    "query_results": None,
    "execution_status": None,
    "current_question": "",
    "should_show_query": False,
    "exec_elapsed": None,
    "question_input": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "available_tables" not in st.session_state:
    try:
        st.session_state.available_tables = load_available_tables()
        st.session_state.tables_error = None
    except Exception as e:
        st.session_state.available_tables = []
        st.session_state.tables_error = str(e)

if "selected_table" not in st.session_state:
    st.session_state.selected_table = (
        st.session_state.available_tables[0] if st.session_state.available_tables else "order"
    )

# ---- Sidebar --------------------------------------------------------------
with st.sidebar:
    st.subheader("Table", anchor=False, divider=False)

    if st.session_state.tables_error:
        st.error(f"Couldn't load tables: {st.session_state.tables_error}", icon=":material/error:")
    elif st.session_state.available_tables:
        st.selectbox(
            "Table to query",
            options=st.session_state.available_tables,
            key="selected_table",
            label_visibility="collapsed",
        )
    else:
        st.caption("No tables found in the `public` schema.")

    if st.session_state.get("schema_table") != st.session_state.selected_table:
        try:
            st.session_state.schema = load_database_schema(st.session_state.selected_table)
            st.session_state.schema_error = None
        except Exception as e:
            st.session_state.schema = None
            st.session_state.schema_error = str(e)
        st.session_state.schema_table = st.session_state.selected_table
        # Selected table changed: downstream question/query state no longer applies.
        st.session_state.current_question = ""
        st.session_state.generated_query = None
        st.session_state.query_results = None
        st.session_state.execution_status = None
        st.session_state.should_show_query = False
        st.session_state.exec_elapsed = None

    st.divider()

    st.subheader("Schema", anchor=False, divider=False)

    with st.expander(f"{st.session_state.selected_table} table columns", icon=":material/table_chart:", expanded=False):
        if st.session_state.schema_error:
            st.error(f"Couldn't load schema: {st.session_state.schema_error}", icon=":material/error:")
        else:
            st.code(st.session_state.schema, language="text")

    if st.button("Refresh schema", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        try:
            st.session_state.available_tables = load_available_tables()
            st.session_state.tables_error = None
            st.session_state.schema = load_database_schema(st.session_state.selected_table)
            st.session_state.schema_error = None
            st.toast("Schema refreshed", icon=":material/check_circle:")
        except Exception as e:
            st.session_state.schema = None
            st.session_state.schema_error = str(e)
            st.toast("Couldn't refresh schema", icon=":material/error:")
        st.rerun()

    st.divider()

    st.subheader("Recent questions", anchor=False, divider=False)
    if st.session_state.questions:
        with st.container(height=250, border=False):
            for i, q in enumerate(reversed(st.session_state.questions)):
                if st.button(q, key=f"hist_{i}", icon=":material/history:", width="stretch"):
                    st.session_state.question_input = q
                    start_new_question(q)
        if st.button("Clear history", icon=":material/delete:", width="stretch"):
            st.session_state.questions = []
            st.toast("History cleared", icon=":material/check_circle:")
            st.rerun()
    else:
        st.caption("Questions you ask will show up here for quick re-use.")

    st.divider()
    with st.expander("About this app", icon=":material/info:", expanded=False):
        st.caption(
            "Describe what you want to know in plain English. GPT turns it into "
            f"a PostgreSQL query against your Supabase `{st.session_state.selected_table}` table, "
            "which you can review before running."
        )
    st.caption("SQL Query Generator · v2.0")

# ---- Hero header ------------------------------------------------------
with st.container(key="hero_box"):
    st.markdown("# :material/database: SQL query generator")
    st.caption("Ask a question in plain English — get SQL, run it, and explore the results.")

# ---- Ask a question --------------------------------------------------
with st.container(border=True):
    st.markdown("#### :material/edit_note: Ask a question")

    if not st.session_state.questions:
        st.caption("Not sure where to start? Try one of these:")
        with st.container(horizontal=True):
            for i, example in enumerate(EXAMPLE_QUESTIONS):
                if st.button(example, key=f"ex_{i}"):
                    st.session_state.question_input = example
                    start_new_question(example)

    with st.form("ask_form"):
        st.text_input(
            "Your question",
            key="question_input",
            placeholder="e.g. What were the top 5 products by revenue last month?",
            help="Describe what you want to know — no SQL knowledge needed.",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "Generate SQL", type="primary", icon=":material/auto_awesome:", width="stretch"
        )

    if submitted:
        question = st.session_state.question_input.strip()
        if question:
            start_new_question(question)
        else:
            st.warning("Type a question before generating a query.", icon=":material/warning:")

# ---- Generate SQL -----------------------------------------------------
if st.session_state.current_question:
    if st.session_state.generated_query is None:
        with st.status("Generating SQL query…", expanded=True) as status:
            try:
                client = get_openai_client()
                schema = st.session_state.schema
                st.write(f"Question: _{st.session_state.current_question}_")

                table_name = st.session_state.selected_table
                prompt = (
                    f"Generate a PostgreSQL query based on this schema:\n{schema}\n\n"
                    f"Question: {st.session_state.current_question}\n\n"
                    f"IMPORTANT: Always use 'public.{table_name}' (with schema prefix) instead of "
                    f"just '{table_name}' to avoid reserved keyword issues.\n\nReturn only the SQL query."
                )

                response = client.responses.create(model="gpt-4o-mini", input=prompt)
                st.session_state.generated_query = clean_sql_response(response.output_text)
                status.update(label="SQL query generated", state="complete")
            except Exception as e:
                status.update(label="Failed to generate query", state="error")
                st.error(f"Error generating query: {str(e)}", icon=":material/error:")
                st.info("Make sure your OPENAI_API_KEY is set in your .env file", icon=":material/key:")

    if st.session_state.generated_query and st.session_state.should_show_query:
        with st.container(border=True):
            st.markdown("#### :material/code: Generated SQL query")
            st.code(st.session_state.generated_query, language="sql")
            st.caption("Hover the code block to copy it.")

            with st.container(horizontal=True):
                execute_clicked = st.button(
                    "Execute query", type="primary", icon=":material/play_arrow:"
                )
                if st.button("Clear results", icon=":material/refresh:"):
                    st.session_state.generated_query = None
                    st.session_state.query_results = None
                    st.session_state.execution_status = None
                    st.session_state.current_question = ""
                    st.session_state.should_show_query = False
                    st.session_state.exec_elapsed = None
                    st.rerun()

            if execute_clicked:
                with st.status("Running query on Supabase…", expanded=False) as status:
                    start = time.time()
                    try:
                        st.session_state.query_results = execute_query(st.session_state.generated_query)
                        st.session_state.execution_status = "success"
                        st.session_state.exec_elapsed = time.time() - start
                        status.update(
                            label=f"Query completed in {st.session_state.exec_elapsed:.2f}s",
                            state="complete",
                        )
                    except Exception as e:
                        st.session_state.execution_status = "error"
                        st.session_state.query_results = str(e)
                        status.update(label="Query failed", state="error")

        # ---- Results ----------------------------------------------------
        if st.session_state.execution_status == "success" and st.session_state.query_results is not None:
            result_df = st.session_state.query_results

            with st.container(border=True):
                st.markdown("#### :material/table_chart: Results")

                tab_table, tab_query = st.tabs(["Table", "Query"])

                with tab_table:
                    if len(result_df) == 0:
                        st.info("No results returned from the query.", icon=":material/info:")
                    else:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Rows", len(result_df))
                        m2.metric("Columns", len(result_df.columns))
                        m3.metric(
                            "Runtime",
                            f"{st.session_state.exec_elapsed:.2f}s" if st.session_state.exec_elapsed else "—",
                        )

                        st.dataframe(result_df, width="stretch")

                        csv_data = result_df.to_csv(index=False)
                        st.download_button(
                            label="Download as CSV",
                            data=csv_data,
                            file_name="query_results.csv",
                            mime="text/csv",
                            icon=":material/download:",
                        )

                with tab_query:
                    st.code(st.session_state.generated_query, language="sql")

        elif st.session_state.execution_status == "error":
            st.error(f"Error executing query: {st.session_state.query_results}", icon=":material/error:")
