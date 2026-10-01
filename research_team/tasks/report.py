"""Task 4: write the final report."""

from crewai import Agent, Task

# How long and detailed each output format should be.
FORMAT_INSTRUCTIONS = {
    "Research Report": (
        "Write a professional report of about 700-900 words. Use these sections where they "
        "fit the topic (skip or rename sections that do not fit): # Title (use a real title), "
        "## Executive Summary, ## Key Findings, ## Analysis, ## Challenges and Risks, "
        "## Outlook, ## Conclusion, ## Sources."
    ),
    "Executive Summary": (
        "Write a short executive summary of about 300-450 words: a title, a summary "
        "paragraph, 4-6 key points as bullets, a one-paragraph conclusion, and ## Sources."
    ),
    "Research Brief": (
        "Write a concise brief of about 500-700 words: a title, ## Summary, ## Key Findings "
        "(short bullets), ## Risks and Caveats, ## Conclusion, and ## Sources."
    ),
}


def create_report_task(agent: Agent, fact_check_task: Task, topic: str, output_format: str) -> Task:
    """Ask the writer for the final Markdown report."""
    format_text = FORMAT_INSTRUCTIONS.get(output_format, FORMAT_INSTRUCTIONS["Research Report"])
    return Task(
        description=(
            f"Topic: {topic}\n\n"
            "Using ONLY the verified research from the previous task, write the final document.\n"
            f"{format_text}\n\n"
            "RULES:\n"
            "- Do not invent facts, numbers, quotes, or URLs.\n"
            "- Use VERIFIED claims freely; mention PARTIALLY VERIFIED claims with a clear caveat; "
            "never use REMOVED claims.\n"
            "- Attribute facts to their sources in the text.\n"
            "- The Sources section must list each source as a Markdown link: "
            "- [Source title](full URL). Only include URLs that appear in the verified research.\n"
            "- Output clean Markdown only. Do not wrap the whole answer in a code block."
        ),
        expected_output="A complete, well-structured Markdown document ending with a ## Sources section.",
        agent=agent,
        context=[fact_check_task],
    )
