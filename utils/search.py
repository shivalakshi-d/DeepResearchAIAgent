"""
Web Search Module for Deep Research AI Agent
"""

import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web and return a list of results.
    Each result contains title, URL, and snippet.
    """

    results = []

    if not query or not query.strip():
        logger.warning("Search query is empty.")
        return results

    try:
        logger.info("Searching the web for: %s", query)

        with DDGS() as ddgs:
            raw_results = ddgs.text(
                query.strip(),
                max_results=max_results
            )

            for result in raw_results:
                title = result.get("title", "")
                url = result.get("href", "")
                snippet = result.get("body", "")

                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })

        logger.info(
            "Web search completed. Results found: %d",
            len(results)
        )

    except Exception:
        logger.exception("Web search failed for query: %s", query)

    return results