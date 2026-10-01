"""Agent 3: Fact Checker."""

from crewai import Agent


def create_fact_checker(llm, search_tool, max_iter: int) -> Agent:
    """Build the agent that verifies the researcher's claims."""
    return Agent(
        role="Fact Checker",
        goal=(
            "Verify the most important claims by searching again, and separate "
            "verified information from weak, outdated, or unsupported information."
        ),
        backstory=(
            "You are a skeptical fact-checking editor. You look for claims that are "
            "outdated, contradicted by other sources, or not supported by the cited "
            "source. You verify with fresh searches and you never invent evidence."
        ),
        tools=[search_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=max_iter,
    )
