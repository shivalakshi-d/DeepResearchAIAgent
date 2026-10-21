"""
FAST web scraper for Deep Research Agent
"""

import requests
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 8


def fetch_article_content(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # REMOVE NOISE
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        text = re.sub(r"\s+", " ", text)

        # VERY IMPORTANT FOR SPEED
        return text[:1200]

    except Exception as e:

        logger.warning(f"Scraping failed: {url} | {e}")

        return None


def batch_fetch(urls, max_articles=2):

    articles = []

    for url in urls[:max_articles]:

        logger.info(f"Fetching: {url}")

        content = fetch_article_content(url)

        if content:

            articles.append({
                "url": url,
                "content": content
            })

    return articles