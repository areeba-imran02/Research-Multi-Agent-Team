"""Task 1: create the research plan."""

from crewai import Agent, Task


def create_planning_task(agent: Agent, topic: str, num_questions: int) -> Task:
    """Ask the planner for a structured research plan."""
    return Task(
        description=(
            f"Research topic: {topic}\n\n"
            f"Create a research plan with exactly {num_questions} focused research questions.\n"
            "You may run one or two quick searches to understand the topic.\n"
            "For each question give: why it matters, and 1-2 suggested search queries.\n"
            "Also list the important areas to cover (for example: current state, "
            "statistics, benefits, risks, recent developments, future outlook)."
        ),
        expected_output=(
            "A structured plan in Markdown with: 1) a one-paragraph scope of the topic, "
            f"2) {num_questions} numbered research questions, each with 'Why it matters' "
            "and 'Suggested searches', 3) a short list of key areas to cover."
        ),
        agent=agent,
    )
