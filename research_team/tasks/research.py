"""Task 2: collect evidence from the web."""

from crewai import Agent, Task


def create_research_task(agent: Agent, planning_task: Task, min_searches: int) -> Task:
    """Ask the researcher to answer the planner's questions using web search."""
    return Task(
        description=(
            "Use the research plan from the previous task. For each research question, "
            f"use the Web Search tool. Run at least {min_searches} different searches in total "
            "(never repeat the same query).\n"
            "Collect facts and statistics, prefer recent sources, and record the source "
            "title and the exact URL for every finding.\n"
            "Keep notes compact: at most 2 findings per question, one or two lines each.\n"
            "RULES: Only record information that appears in search results. "
            "Never invent a URL or a number. If a question cannot be answered from "
            "the results, write 'No reliable information found'. "
            "If a search returns SEARCH_ERROR, try a different query."
        ),
        expected_output=(
            "Findings grouped by research question. Each finding has: the fact or "
            "statistic, the date if known, the source title, and the source URL."
        ),
        agent=agent,
        context=[planning_task],
    )
