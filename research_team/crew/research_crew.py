"""Builds the four-agent crew and runs it step by step (sequentially)."""

import logging
import re
from typing import Callable, Dict, List, Optional

from crewai import Crew, Process

from agents.fact_checker import create_fact_checker
from agents.planner import create_planner
from agents.report_writer import create_report_writer
from agents.researcher import create_researcher
from config.groq_config import ConfigError, get_llm, redact
from tasks.fact_check import create_fact_check_task
from tasks.planning import create_planning_task
from tasks.report import create_report_task
from tasks.research import create_research_task
from tools.web_search import URL_PATTERN, build_search_tool, normalize_url

logger = logging.getLogger(__name__)

# How much work each depth level asks for (tuned for the Groq free plan).
DEPTH_SETTINGS = {
    "Quick":    {"questions": 3, "results_per_search": 3, "min_searches": 3, "checks": 1},
    "Standard": {"questions": 4, "results_per_search": 3, "min_searches": 4, "checks": 2},
    "Detailed": {"questions": 5, "results_per_search": 4, "min_searches": 5, "checks": 2},
}

# Token budget per answer. The writer needs more room than the other agents.
WORKER_MAX_TOKENS = 1500
WRITER_MAX_TOKENS = 3000


class ResearchError(Exception):
    """Raised when the research run fails in a way we can explain to the user."""


def friendly_error(exc: Exception) -> str:
    """Turn a technical error into a short message without exposing secrets."""
    text = redact(str(exc)).lower()
    name = type(exc).__name__.lower()
    if "request too large" in text or "413" in text:
        return ("This request is too big for the free Groq limit. "
                "Choose the Quick depth and try again.")
    if "ratelimit" in name or "rate limit" in text or "429" in text:
        return ("Groq is limiting requests right now. "
                "Wait one minute and try again, or choose the Quick depth.")
    if "authentication" in name or "401" in text or "invalid api key" in text:
        return "Groq rejected the API key. Check GROQ_API_KEY in your secrets."
    if "timeout" in name or "timed out" in text:
        return "The request timed out. Please try again."
    return "The research team hit an unexpected problem. Please try again."


def clean_report(text: str) -> str:
    """Remove a wrapping ```markdown code fence if the model added one."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
    return text.strip()


def split_sources(report: str, search_log: Dict) -> Dict[str, List]:
    """Compare links in the report with URLs that really came from search.

    verified   = cited in the report AND returned by the search tool
    unverified = cited in the report but never seen in search results
    """
    seen = search_log["sources"]
    cited = []
    for url in URL_PATTERN.findall(report):
        clean = normalize_url(url)
        if clean not in cited:
            cited.append(clean)
    verified = [{"title": seen[url], "url": url} for url in cited if url in seen]
    unverified = [url for url in cited if url not in seen]
    return {"verified": verified, "unverified": unverified}


def run_research(
    topic: str,
    depth: str,
    output_format: str,
    on_progress: Optional[Callable[[int], None]] = None,
) -> Dict:
    """Run Planner -> Researcher -> Fact Checker -> Writer and return the result.

    on_progress(n) is called each time one agent finishes (n = finished count).
    """
    settings = DEPTH_SETTINGS.get(depth, DEPTH_SETTINGS["Quick"])
    llm = get_llm(WORKER_MAX_TOKENS)               # may raise ConfigError
    writer_llm = get_llm(WRITER_MAX_TOKENS)

    # The tool fills this log while the agents search.
    search_log: Dict = {"queries": [], "sources": {}}
    search_tool = build_search_tool(settings["results_per_search"], search_log)

    # 1) Agents
    planner = create_planner(llm, search_tool)
    researcher = create_researcher(llm, search_tool, max_iter=settings["min_searches"] + 2)
    fact_checker = create_fact_checker(llm, search_tool, max_iter=settings["checks"] + 2)
    writer = create_report_writer(writer_llm)

    # 2) Tasks (each one receives the previous task's output as context)
    planning_task = create_planning_task(planner, topic, settings["questions"])
    research_task = create_research_task(researcher, planning_task, settings["min_searches"])
    fact_check_task = create_fact_check_task(fact_checker, research_task, settings["checks"])
    report_task = create_report_task(writer, fact_check_task, topic, output_format)

    # 3) Progress tracking
    finished = {"count": 0}

    def handle_task_done(_task_output) -> None:
        finished["count"] += 1
        if on_progress:
            on_progress(finished["count"])

    # 4) The crew: sequential = tasks run one after another, in order.
    crew = Crew(
        agents=[planner, researcher, fact_checker, writer],
        tasks=[planning_task, research_task, fact_check_task, report_task],
        process=Process.sequential,
        task_callback=handle_task_done,
        max_rpm=10,
        verbose=False,
    )

    try:
        output = crew.kickoff()
    except ConfigError:
        raise
    except Exception as exc:
        detail = f"{type(exc).__name__}: {redact(str(exc))[:400]}"
        logger.error("Crew run failed: %s", detail)
        raise ResearchError(f"{friendly_error(exc)}\n\nTechnical detail: {detail}") from exc

    report = clean_report(getattr(output, "raw", None) or str(output))

    # Safety checks on unexpected output
    if not search_log["queries"]:
        raise ResearchError("The agents did not use the web search tool, so the result cannot be trusted.")
    if not search_log["sources"]:
        raise ResearchError("Web search returned no usable results (the search service may be busy). Please wait a minute and try again.")
    if len(report) < 200:
        raise ResearchError("The Report Writer returned an unexpectedly short result. Please try again.")

    return {
        "report": report,
        "sources": split_sources(report, search_log),
        "queries": search_log["queries"],
        "source_count": len(search_log["sources"]),
    }
