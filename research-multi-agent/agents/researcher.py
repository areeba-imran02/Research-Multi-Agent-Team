"""Agent 2: Web Researcher."""

from crewai import Agent


def create_researcher(llm, search_tool, max_iter: int) -> Agent:
    """Build the agent that searches the web and collects evidence."""
    return Agent(
        role="Web Researcher",
        goal=(
            "Answer each research question using real web search results. "
            "Collect facts, statistics, and the exact source titles and URLs."
        ),
        backstory=(
            "You are a careful online researcher. You never rely on memory alone. "
            "You search, read the results, and only record what the results say. "
            "You prefer recent, reputable sources and always note the source URL."
        ),
        tools=[search_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=max_iter,
    )
