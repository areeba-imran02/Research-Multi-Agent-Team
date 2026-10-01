"""Task 3: verify the researcher's findings."""

from crewai import Agent, Task


def create_fact_check_task(agent: Agent, research_task: Task, num_checks: int) -> Task:
    """Ask the fact checker to verify the most important claims."""
    return Task(
        description=(
            "Review the collected research from the previous task.\n"
            f"Pick the {num_checks} most important claims and "
            "verify them using the Web Search tool (look for a second, independent source). "
            "Never repeat the same query.\n"
            "Check whether each cited source really supports its claim, and flag claims "
            "that are outdated, weak, contradictory, or unsupported.\n"
            "Keep the output compact. Copy the other findings over as they are, "
            "marked PARTIALLY VERIFIED if you did not check them.\n"
            "RULES: Never invent evidence or URLs. Keep only URLs that appeared in the research "
            "or in your own search results."
        ),
        expected_output=(
            "A clean verified dataset in Markdown with four sections: "
            "1) VERIFIED (claim, supporting source titles and URLs), "
            "2) PARTIALLY VERIFIED (claim, source URL, and what is uncertain), "
            "3) REMOVED (claim and the reason it was removed), "
            "4) a short list of caveats the writer must mention."
        ),
        agent=agent,
        context=[research_task],
    )
