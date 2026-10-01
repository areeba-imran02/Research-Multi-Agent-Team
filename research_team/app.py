"""Research Multi-Agent Team - Streamlit front end.

This file only handles the screen. All agent logic lives in the other folders.
"""

import logging
import os
import time
from urllib.parse import urlparse

# Turn off CrewAI's anonymous telemetry (keeps logs quiet on Streamlit Cloud).
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import streamlit as st

from config.groq_config import ConfigError, missing_secrets, redact, set_wait_notifier
from crew.research_crew import DEPTH_SETTINGS, ResearchError, run_research

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Research Multi-Agent Team",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# Palette: ink #0d1320 | panel #141c2e | line #25304a | teal #2dd4bf (done, primary)
#          amber #f5b84b (working) | coral #f87171 (error) | muted #8b95ad
# Type:    Newsreader (headings, report) + Instrument Sans (interface)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');

html, body, [class*="css"], .stMarkdown, button, input, textarea, select {
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1080px; padding-top: 2rem; padding-bottom: 4rem; }

/* ---- Masthead ---- */
.masthead { padding: .4rem 0 1.4rem 0; border-bottom: 1px solid #25304a; margin-bottom: 1.6rem; }
.masthead h1 {
  font-family: 'Newsreader', Georgia, serif; font-weight: 500;
  font-size: 2.6rem; line-height: 1.1; letter-spacing: -0.015em; margin: 0 0 .5rem 0;
}
.masthead p { margin: 0; color: #8b95ad; font-size: 1.05rem; max-width: 40rem; }
.pills { display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 1rem; }
.pill {
  font-size: .78rem; padding: .18rem .65rem; border-radius: 999px;
  border: 1px solid #25304a; color: #aab3c8; background: #141c2e;
}

/* ---- Headings ---- */
.section-title {
  font-family: 'Newsreader', Georgia, serif; font-size: 1.45rem; font-weight: 500;
  margin: 2rem 0 .2rem 0;
}
.section-sub { color: #8b95ad; font-size: .92rem; margin-bottom: .9rem; }

/* ---- Inputs ---- */
.stTextArea textarea {
  font-size: 1.05rem; border-radius: 12px; border: 1px solid #25304a; background: #141c2e;
}
.stTextArea textarea:focus { border-color: #2dd4bf; box-shadow: 0 0 0 1px #2dd4bf; }
div[data-baseweb="select"] > div { border-radius: 10px; background: #141c2e; border-color: #25304a; }
.stRadio [role="radiogroup"] { gap: .4rem; }

/* ---- Buttons ---- */
div.stButton > button {
  border-radius: 10px; border: 1px solid #25304a; background: #141c2e; color: #cfd5e4;
  font-size: .86rem; padding: .35rem .8rem; transition: border-color .15s, color .15s;
}
div.stButton > button:hover { border-color: #2dd4bf; color: #2dd4bf; }
div.stButton > button:focus-visible { outline: 2px solid #2dd4bf; outline-offset: 2px; }
div.stButton > button[kind="primary"] {
  background: #2dd4bf; color: #06201c; border: none; font-weight: 600;
  font-size: 1rem; padding: .65rem 1.8rem;
}
div.stButton > button[kind="primary"]:hover { background: #5eead4; color: #06201c; }
div.stDownloadButton > button {
  border-radius: 10px; border: 1px solid #2dd4bf; background: transparent; color: #2dd4bf;
  font-weight: 600;
}
div.stDownloadButton > button:hover { background: rgba(45,212,191,.1); }

/* ---- Pipeline: four stages joined by one rail ---- */
.pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; position: relative; margin: .4rem 0 1rem 0; }
.step { position: relative; padding: 0 1rem 0 0; }
.step::before {            /* the rail */
  content: ""; position: absolute; top: 15px; left: 32px; right: 0; height: 2px; background: #25304a;
}
.step:last-child::before { display: none; }
.step-completed::before { background: #2dd4bf; }
.node {
  position: relative; z-index: 1; width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .85rem; font-weight: 600; background: #0d1320; border: 2px solid #25304a; color: #8b95ad;
}
.step-running .node { border-color: #f5b84b; color: #f5b84b; animation: pulse 1.6s ease-in-out infinite; }
.step-completed .node { border-color: #2dd4bf; background: #2dd4bf; color: #06201c; }
.step-error .node { border-color: #f87171; background: #f87171; color: #2a0a0a; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(245,184,75,.45); } 50% { box-shadow: 0 0 0 8px rgba(245,184,75,0); } }
.step-name { font-weight: 600; margin-top: .7rem; font-size: 1rem; }
.step-desc { color: #8b95ad; font-size: .86rem; margin-top: .15rem; min-height: 2.4rem; }
.state { font-size: .8rem; margin-top: .35rem; color: #8b95ad; }
.step-running .state { color: #f5b84b; }
.step-completed .state { color: #2dd4bf; }
.step-error .state { color: #f87171; }
@media (max-width: 760px) {
  .pipeline { grid-template-columns: 1fr; row-gap: 1.1rem; }
  .step::before { display: none; }
  .step { display: grid; grid-template-columns: 32px 1fr; column-gap: .8rem; }
  .step .node { grid-row: span 3; }
  .step-name { margin-top: 0; }
  .step-desc { min-height: 0; }
}
@media (prefers-reduced-motion: reduce) { .step-running .node { animation: none; } }

/* ---- Result stats ---- */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .6rem 0 1.2rem 0; }
.stat { padding: .85rem 1rem; border: 1px solid #25304a; border-radius: 12px; background: #141c2e; }
.stat b { display: block; font-family: 'Newsreader', Georgia, serif; font-size: 1.7rem; font-weight: 500; }
.stat span { color: #8b95ad; font-size: .84rem; }
@media (max-width: 760px) { .stats { grid-template-columns: repeat(2, 1fr); } }

/* ---- Report reading surface ---- */
.report-wrap [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; border-color: #25304a; background: #121a2b; }
.report-wrap .stMarkdown p, .report-wrap .stMarkdown li {
  font-family: 'Newsreader', Georgia, serif; font-size: 1.12rem; line-height: 1.7; max-width: 46rem;
}
.report-wrap .stMarkdown h1, .report-wrap .stMarkdown h2, .report-wrap .stMarkdown h3 {
  font-family: 'Newsreader', Georgia, serif; font-weight: 500; letter-spacing: -0.01em;
}
.report-wrap .stMarkdown h2 { margin-top: 1.6rem; border-bottom: 1px solid #25304a; padding-bottom: .3rem; }
.report-wrap .stMarkdown a { color: #5eead4; }

/* ---- Source rows ---- */
.src { padding: .7rem .9rem; border: 1px solid #25304a; border-radius: 10px; background: #141c2e; margin-bottom: .5rem; }
.src a { color: #e6e9f0; font-weight: 500; text-decoration: none; }
.src a:hover { color: #2dd4bf; }
.src small { display: block; color: #8b95ad; margin-top: .1rem; }

/* ---- Tabs & sidebar ---- */
.stTabs [data-baseweb="tab"] { font-weight: 500; }
[data-testid="stSidebar"] { border-right: 1px solid #25304a; }
.side-note { color: #8b95ad; font-size: .86rem; line-height: 1.5; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
AGENTS = [
    ("Research Planner", "Turns your topic into focused questions"),
    ("Web Researcher", "Searches the web and collects evidence"),
    ("Fact Checker", "Re-checks the key claims with new searches"),
    ("Report Writer", "Writes the report from verified facts only"),
]
STATE_LABELS = {"waiting": "Waiting", "running": "Working", "completed": "Done", "error": "Failed"}
DEPTH_NOTES = {
    "Quick": "Fastest. Best for the free plan.",
    "Standard": "Balanced coverage.",
    "Detailed": "Most thorough. Takes longer.",
}
FORMATS = {
    "Research Report": "Full report with sections (about 800 words)",
    "Executive Summary": "One page for busy readers (about 400 words)",
    "Research Brief": "Short brief with findings and risks (about 600 words)",
}
EXAMPLES = [
    "Impact of artificial intelligence on education",
    "Renewable energy adoption in Pakistan",
    "Benefits and risks of intermittent fasting",
]


def pipeline_html(states: list) -> str:
    parts = []
    for index, ((name, description), state) in enumerate(zip(AGENTS, states), start=1):
        mark = "✓" if state == "completed" else ("!" if state == "error" else str(index))
        parts.append(
            f'<div class="step step-{state}"><div class="node">{mark}</div>'
            f'<div class="step-name">{name}</div>'
            f'<div class="step-desc">{description}</div>'
            f'<div class="state">{STATE_LABELS[state]}</div></div>'
        )
    return '<div class="pipeline">' + "".join(parts) + "</div>"


def render_workflow(slot, states: list) -> None:
    slot.markdown(pipeline_html(states), unsafe_allow_html=True)


def use_example(text: str) -> None:
    st.session_state["topic"] = text


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### How it works")
    st.markdown(
        '<div class="side-note">Four AI agents work one after another. '
        "Each one hands its notes to the next, so the final report only contains "
        "claims that were searched and checked.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Tips")
    st.markdown(
        '<div class="side-note">'
        "• Start with <b>Quick</b> to test.<br>"
        "• Name the place, period or group in your topic for sharper results.<br>"
        "• If Groq's free limit is reached, the app waits and continues by itself."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Connection")
    if missing_secrets():
        st.warning("GROQ_API_KEY is missing")
    else:
        st.success("Groq key found")

# ---------------------------------------------------------------------------
# Header + inputs
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="masthead"><h1>Research Multi-Agent Team</h1>'
    "<p>Give a topic. Four agents plan, search, fact-check and write a sourced report for you.</p>"
    '<div class="pills"><span class="pill">Free web search</span>'
    '<span class="pill">Powered by Groq</span>'
    '<span class="pill">Every link checked against real search results</span></div></div>',
    unsafe_allow_html=True,
)

st.text_area(
    "What do you want to research?",
    key="topic",
    placeholder="For example: Impact of artificial intelligence on education",
    height=110,
)

st.caption("Or try an example:")
example_cols = st.columns(len(EXAMPLES))
for column, example in zip(example_cols, EXAMPLES):
    column.button(example, key=f"ex_{example}", on_click=use_example, args=(example,), use_container_width=True)

left, right = st.columns(2)
with left:
    depth = st.radio("Research depth", list(DEPTH_SETTINGS.keys()), index=0, horizontal=True)
    cfg = DEPTH_SETTINGS[depth]
    st.caption(f"{DEPTH_NOTES.get(depth, '')} {cfg['questions']} questions, {cfg['min_searches']}+ searches.")
with right:
    output_format = st.selectbox("Output format", list(FORMATS.keys()))
    st.caption(FORMATS[output_format])

start_clicked = st.button("Start research", type="primary")

# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title">Agent workflow</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Follow each agent as it finishes its part.</div>', unsafe_allow_html=True)
workflow_slot = st.empty()
progress_slot = st.empty()
wait_slot = st.empty()
states = ["waiting"] * 4
render_workflow(workflow_slot, states)


def on_wait(seconds: int) -> None:
    """Shown while the app pauses for Groq's free-plan rate limit."""
    if seconds > 0:
        wait_slot.info(f"Groq's free limit was reached. Continuing automatically in {seconds}s.")
    else:
        wait_slot.empty()


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if start_clicked:
    clean_topic = (st.session_state.get("topic") or "").strip()
    missing = missing_secrets()

    if not clean_topic:
        st.error("Enter a research topic above, or pick an example.")
    elif missing:
        st.error(
            f"Missing secret: {', '.join(missing)}. Add it in Streamlit Cloud under "
            "App > Settings > Secrets, then reboot the app."
        )
    else:
        st.session_state.pop("result", None)
        states = ["running", "waiting", "waiting", "waiting"]
        render_workflow(workflow_slot, states)
        progress_bar = progress_slot.progress(0, text=f"{AGENTS[0][0]} is working...")
        started = time.time()

        def on_progress(done: int) -> None:
            """Called by the crew each time an agent finishes."""
            for i in range(4):
                states[i] = "completed" if i < done else ("running" if i == done else "waiting")
            render_workflow(workflow_slot, states)
            if done < 4:
                progress_bar.progress(done / 4, text=f"{AGENTS[done][0]} is working...")
            else:
                progress_bar.progress(1.0, text="Research complete")

        def mark_failed() -> None:
            if "running" in states:
                states[states.index("running")] = "error"
            render_workflow(workflow_slot, states)
            progress_slot.empty()

        set_wait_notifier(on_wait)
        try:
            result = run_research(clean_topic, depth, output_format, on_progress)
            result["elapsed"] = time.time() - started
            result["topic"] = clean_topic
            st.session_state["result"] = result
        except (ConfigError, ResearchError) as exc:
            mark_failed()
            message = redact(str(exc))
            summary, _, detail = message.partition("\n\nTechnical detail:")
            st.error(summary)
            if detail.strip():
                with st.expander("Technical detail (send this if you need help)"):
                    st.code(detail.strip(), language=None)
        except Exception as exc:  # last safety net
            logger.error("Unexpected failure: %s", type(exc).__name__)
            mark_failed()
            st.error("Something unexpected went wrong. Please try again.")
        finally:
            set_wait_notifier(None)
            wait_slot.empty()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
result = st.session_state.get("result")
if result:
    st.markdown('<div class="section-title">Your report</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">Topic: {result.get("topic", "")}</div>',
        unsafe_allow_html=True,
    )

    words = len(result["report"].split())
    verified = result["sources"]["verified"]
    st.markdown(
        '<div class="stats">'
        f'<div class="stat"><b>{len(result["queries"])}</b><span>web searches</span></div>'
        f'<div class="stat"><b>{result["source_count"]}</b><span>sources found</span></div>'
        f'<div class="stat"><b>{len(verified)}</b><span>sources cited</span></div>'
        f'<div class="stat"><b>{format_duration(result.get("elapsed", 0))}</b><span>{words} words written</span></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    tab_report, tab_sources, tab_searches = st.tabs(["Report", "Sources", "Searches"])

    with tab_report:
        st.markdown('<div class="report-wrap">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(result["report"])
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button(
            "Download report (.md)",
            data=result["report"],
            file_name="research_report.md",
            mime="text/markdown",
        )
        with st.expander("Copy the raw Markdown"):
            st.code(result["report"], language="markdown")

    with tab_sources:
        if verified:
            st.caption("These links were cited in the report and also appeared in real search results.")
            for source in verified:
                domain = urlparse(source["url"]).netloc.replace("www.", "")
                st.markdown(
                    f'<div class="src"><a href="{source["url"]}" target="_blank" rel="noopener">'
                    f'{source["title"]}</a><small>{domain}</small></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No cited link could be matched to the search results.")

        unverified = result["sources"]["unverified"]
        if unverified:
            with st.expander("Links in the report that were not found in search results"):
                st.warning("Check these by hand. They may be wrong.")
                for url in unverified:
                    st.code(url, language=None)

    with tab_searches:
        st.caption("Every query the agents sent to the web.")
        for query in result["queries"]:
            st.markdown(f"- {query}")
