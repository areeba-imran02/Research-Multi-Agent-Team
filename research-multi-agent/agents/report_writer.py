"""Agent 4: Report Writer."""

from crewai import Agent


def create_report_writer(llm) -> Agent:
    """Build the agent that writes the final report.

    This agent has NO search tool on purpose: it may only use the
    verified research it is given, so it cannot add unsupported facts.
    """
    return Agent(
        role="Report Writer",
        goal=(
            "Write a clear, professional Markdown report using only the verified "
            "research, with accurate source attribution."
        ),
        backstory=(
            "You are a professional research writer. You never invent facts, "
            "numbers, or links. If evidence is uncertain, you say so plainly. "
            "You only cite URLs that appear in the verified research."
        ),
        tools=[],
        llm=llm,
        allow_delegation=False,
        verbose=False,
        max_iter=4,
    )
