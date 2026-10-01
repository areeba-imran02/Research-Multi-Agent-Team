"""Research Multi-Agent Team - Streamlit front end.

This file only handles the screen. All agent logic lives in the other folders.
"""

import logging
import os

# Turn off CrewAI's anonymous telemetry (keeps logs quiet on Streamlit Cloud).
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import streamlit as st

from config.groq_config import ConfigError, missing_secrets, redact
from crew.research_crew import DEPTH_SETTINGS, ResearchError, run_research

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Research Multi-Agent Team", layout="wide")

# ---------- Styling ----------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { max-width: 1100px; padding-top: 2.2rem; }
.hero {
  padding: 1.8rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
  background: linear-gradient(135deg, rgba(79,70,229,0.12), rgba(14,165,233,0.07));
  border: 1px solid rgba(127,127,127,0.25);
}
.hero h1 { margin: 0 0 .3rem 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; }
.hero p { margin: 0; opacity: .75; font-size: 1.02rem; }
.section-label {
  font-size: .78rem; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; opacity: .6; margin: 1.8rem 0 .7rem 0;
}
.agent-card {
  padding: 1rem 1.1rem; border-radius: 12px; height: 100%;
  background: rgba(127,127,127,0.06); border: 1px solid rgba(127,127,127,0.25);
}
.agent-num { font-size: .8rem; font-weight: 600; opacity: .5; }
.agent-name { font-size: 1.02rem; font-weight: 600; margin: .15rem 0; }
.agent-desc { font-size: .86rem; opacity: .7; margin-bottom: .7rem; min-height: 2.4rem; }
.badge {
  display: inline-block; padding: .15rem .6rem; border-radius: 999px;
  font-size: .75rem; font-weight: 600;
}
.badge-waiting   { background: rgba(107,114,128,.16); color: #6b7280; }
.badge-running   { background: rgba(37,99,235,.15);  color: #2563eb; }
.badge-completed { background: rgba(22,163,74,.15);  color: #16a34a; }
.badge-error     { background: rgba(220,38,38,.15);  color: #dc2626; }
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #4f46e5, #2563eb); border: none;
  font-weight: 600; padding: .6rem 1.6rem; border-radius: 10px;
}
div.stButton > button[kind="primary"]:hover { filter: brightness(1.08); }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Workflow display ----------
AGENTS = [
    ("01", "Research Planner", "Breaks the topic into research questions"),
    ("02", "Web Researcher", "Searches and collects information"),
    ("03", "Fact Checker", "Verifies claims and sources"),
    ("04", "Report Writer", "Creates the final report"),
]
STATE_LABELS = {"waiting": "Waiting", "running": "Running", "completed": "Completed", "error": "Error"}


def render_workflow(slot, states: list) -> None:
    """Draw the four agent cards with their current states."""
    with slot.container():
        columns = st.columns(4)
        for column, (number, name, description), state in zip(columns, AGENTS, states):
            card = (
                f'<div class="agent-card">'
                f'<div class="agent-num">{number}</div>'
                f'<div class="agent-name">{name}</div>'
                f'<div class="agent-desc">{description}</div>'
                f'<span class="badge badge-{state}">{STATE_LABELS[state]}</span>'
                f"</div>"
            )
            column.markdown(card, unsafe_allow_html=True)


def show_config_error(missing: list) -> None:
    """Explain missing secrets without showing any key values."""
    names = ", ".join(missing)
    st.error(
        f"Configuration error: missing secret(s): {names}. "
        "Add them in Streamlit Cloud under App > Settings > Secrets, then reboot the app."
    )


# ---------- Header ----------
st.markdown(
    '<div class="hero"><h1>Research Multi-Agent Team</h1>'
    "<p>AI-powered structured research workspace</p></div>",
    unsafe_allow_html=True,
)

# ---------- Inputs ----------
topic = st.text_area(
    "Research Topic",
    placeholder="Enter your research topic... e.g. Impact of Artificial Intelligence on Education",
    height=100,
)
left, right = st.columns(2)
depth = left.selectbox("Research Depth", list(DEPTH_SETTINGS.keys()), index=1)
output_format = right.selectbox("Output Format", ["Research Report", "Executive Summary", "Research Brief"])
start_clicked = st.button("Start Research", type="primary")

# ---------- Workflow section ----------
st.markdown('<div class="section-label">Agent Workflow</div>', unsafe_allow_html=True)
workflow_slot = st.empty()
progress_slot = st.empty()
states = ["waiting"] * 4
render_workflow(workflow_slot, states)

# ---------- Run ----------
if start_clicked:
    clean_topic = topic.strip()
    missing = missing_secrets()

    if not clean_topic:
        st.error("Please enter a research topic.")
    elif missing:
        show_config_error(missing)
    else:
        st.session_state.pop("result", None)
        states = ["running", "waiting", "waiting", "waiting"]
        render_workflow(workflow_slot, states)
        progress_bar = progress_slot.progress(0, text="Research Planner is working...")

        def on_progress(done: int) -> None:
            """Called by the crew each time an agent finishes."""
            for i in range(4):
                states[i] = "completed" if i < done else ("running" if i == done else "waiting")
            render_workflow(workflow_slot, states)
            if done < 4:
                progress_bar.progress(done / 4, text=f"{AGENTS[done][1]} is working...")
            else:
                progress_bar.progress(1.0, text="Research complete")

        try:
            with st.spinner("The agents are working. This can take a few minutes."):
                st.session_state["result"] = run_research(clean_topic, depth, output_format, on_progress)
                st.session_state["topic"] = clean_topic
        except (ConfigError, ResearchError) as exc:
            if "running" in states:
                states[states.index("running")] = "error"
            render_workflow(workflow_slot, states)
            progress_slot.empty()
            st.error(redact(str(exc)))
        except Exception as exc:  # last safety net
            logger.error("Unexpected failure: %s", type(exc).__name__)
            if "running" in states:
                states[states.index("running")] = "error"
            render_workflow(workflow_slot, states)
            progress_slot.empty()
            st.error("Something unexpected went wrong. Please try again.")

# ---------- Results ----------
result = st.session_state.get("result")
if result:
    st.markdown('<div class="section-label">Final Research Report</div>', unsafe_allow_html=True)
    st.caption(
        f"{len(result['queries'])} web searches run by the agents, "
        f"{result['source_count']} sources found."
    )
    with st.container(border=True):
        st.markdown(result["report"])

    st.download_button(
        "Download Report",
        data=result["report"],
        file_name="research_report.md",
        mime="text/markdown",
    )

    st.markdown('<div class="section-label">Sources</div>', unsafe_allow_html=True)
    verified = result["sources"]["verified"]
    if verified:
        for source in verified:
            st.markdown(f"- [{source['title']}]({source['url']})")
    else:
        st.info("No cited sources could be matched to the search results.")

    unverified = result["sources"]["unverified"]
    if unverified:
        with st.expander("Links in the report that were not found in search results"):
            st.warning("Please check these manually. They may be incorrect.")
            for url in unverified:
                st.code(url, language=None)

    with st.expander("Search queries used by the agents"):
        for query in result["queries"]:
            st.markdown(f"- {query}")
