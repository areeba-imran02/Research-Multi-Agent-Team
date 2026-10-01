"""Agent 1: Research Planner."""

from crewai import Agent


def create_planner(llm, search_tool) -> Agent:
    """Build the agent that turns a topic into a research plan."""
    return Agent(
        role="Research Planner",
        goal=(
            "Break a research topic into focused, answerable research questions "
            "and a clear plan for the researcher."
        ),
        backstory=(
            "You are a senior research lead. You are great at scoping a topic: "
            "deciding what matters, what to ask, and what evidence would answer it. "
            "You may run one or two quick searches to understand the topic, "
            "but you do not write findings yourself."
        ),
        tools=[search_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=6,  # stops the agent from looping forever
    )
