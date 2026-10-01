"""Task 1: create the research plan."""

from crewai import Agent, Task


def create_planning_task(agent: Agent, topic: str, num_questions: int) -> Task:
    """Ask the planner for a structured research plan."""
    return Task(
        description=(
            f"Research topic: {topic}\n\n"
            f"Create a research plan with exactly {num_questions} focused research questions.\n"
            "You may run one quick search to understand the topic.\n"
            "For each question give: why it matters (one line), and one suggested search query.\n"
            "Keep the whole plan under 250 words."
        ),
        expected_output=(
            "A short Markdown plan with: 1) a two-sentence scope, "
            f"2) {num_questions} numbered research questions, each with 'Why it matters' "
            "and 'Suggested search'."
        ),
        agent=agent,
    )
