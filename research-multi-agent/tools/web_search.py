"""The web-search tool that the agents use.

It searches DuckDuckGo through the free "ddgs" package, so NO search API key
is needed. We wrap it so that we can:
  1. return short, clean results (saves tokens),
  2. retry once and return a clear error message if search fails,
  3. remember every query and URL, so the app can show real sources.
"""

import logging
import re
import time
from typing import Dict

from crewai.tools import tool
from ddgs import DDGS

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s<>\"'\)\]]+")


def normalize_url(url: str) -> str:
    """Tidy a URL so two spellings of the same link compare as equal."""
    return url.strip().rstrip(".,;:").rstrip("/")


def build_search_tool(results_per_search: int, search_log: Dict):
    """Create the 'Web Search' tool.

    search_log is a dict the tool fills in while agents work:
        {"queries": [list of queries], "sources": {url: title}}
    """

    @tool("Web Search")
    def web_search(query: str) -> str:
        """Search the web and return titles, URLs and snippets.
        Use short, specific queries. Run several searches for different questions."""
        search_log["queries"].append(query)

        results = None
        for attempt in range(2):  # try up to 2 times
            try:
                results = DDGS().text(query, max_results=results_per_search)
                break
            except Exception as exc:
                logger.warning("Search attempt %s failed: %s", attempt + 1, type(exc).__name__)
                time.sleep(2)

        if results is None:
            return "SEARCH_ERROR: the search service failed. Try again with different wording."
        if not results:
            return "No results found for this query. Try different wording."

        lines = []
        for number, item in enumerate(results, start=1):
            title = item.get("title", "Untitled")
            link = item.get("href", "")
            if link:
                search_log["sources"][normalize_url(link)] = title
            lines.append(
                f"[{number}] {title}\n"
                f"URL: {link}\n"
                f"Snippet: {item.get('body', '')}"
            )
        return "\n\n".join(lines)

    return web_search
