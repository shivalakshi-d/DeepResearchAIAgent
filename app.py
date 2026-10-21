"""
Deep Research AI Agent
Flask backend for web research and image analysis.
"""

import json
import logging
import os
from datetime import datetime
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from utils import search_web, batch_fetch, summarize_research
from utils.summarizer import analyze_image


# =========================================
# CONFIGURATION
# =========================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-secret-key"
)

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "search_history.json")

history_lock = Lock()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# =========================================
# HISTORY HELPERS
# =========================================

def read_search_history():
    """Read saved history safely."""

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)

        return history if isinstance(history, list) else []

    except (json.JSONDecodeError, OSError) as error:
        logger.error("Could not read search history: %s", error)
        return []


def write_search_history(history):
    """Write history safely."""

    temporary_file = HISTORY_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4, ensure_ascii=False)

    os.replace(temporary_file, HISTORY_FILE)


def save_search_history(query, report, sources):
    """Save a completed research report."""

    entry = {
        "query": query,
        "report": report,
        "sources": sources,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with history_lock:
        history = read_search_history()
        history.append(entry)
        write_search_history(history)

    logger.info("Saved search history: %s", query)


# =========================================
# HOME
# =========================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================
# RESEARCH
# =========================================

@app.route("/research", methods=["POST"])
def research():

    try:
        # -------------------------------------
        # READ REQUEST
        # -------------------------------------

        if request.content_type and request.content_type.startswith(
            "multipart/form-data"
        ):
            topic = (
                request.form.get("query")
                or request.form.get("topic")
                or ""
            ).strip()

            image_file = request.files.get("image")

        else:
            data = request.get_json(silent=True) or {}

            topic = (
                data.get("query")
                or data.get("topic")
                or ""
            ).strip()

            image_file = None

        # -------------------------------------
        # IMAGE ANALYSIS
        # -------------------------------------

        if image_file and image_file.filename:

            if image_file.mimetype not in ALLOWED_IMAGE_TYPES:
                return jsonify({
                    "success": False,
                    "error": "Please upload a JPG, PNG, or WEBP image."
                }), 400

            image_bytes = image_file.read()

            if not image_bytes:
                return jsonify({
                    "success": False,
                    "error": "The uploaded image is empty."
                }), 400

            if not topic:
                topic = "Describe this image in detail."

            logger.info("Analyzing image using LLaVA.")

            result = analyze_image(topic, image_bytes)

            if result.get("model_used") == "error":
                logger.error(
                    "Image analysis failed: %s",
                    result.get("report", "Unknown error")
                )

                return jsonify({
                    "success": False,
                    "error": result.get(
                        "report",
                        "Image analysis failed."
                    )
                }), 500

            save_search_history(
                topic,
                result.get("report", ""),
                []
            )

            return jsonify({
                "success": True,
                "topic": topic,
                "report": result.get("report", ""),
                "model_used": result.get("model_used", "llava"),
                "tokens_used": result.get("tokens_used", 0),
                "sources_analyzed": 0,
                "sources": [],
            })

        # -------------------------------------
        # VALIDATE TEXT QUERY
        # -------------------------------------

        if not topic:
            return jsonify({
                "success": False,
                "error": "Please enter a topic or upload an image."
            }), 400

        # -------------------------------------
        # STEP 1: SEARCH
        # -------------------------------------

        logger.info("Searching the web for: %s", topic)

        search_results = search_web(topic, max_results=3)

        if not search_results:
            return jsonify({
                "success": False,
                "error": "No search results found. Please try another topic."
            }), 404

        urls = [
            result.get("url")
            for result in search_results
            if result.get("url")
        ]

        if not urls:
            return jsonify({
                "success": False,
                "error": "The search did not return any usable URLs."
            }), 404

        # -------------------------------------
        # STEP 2: FETCH ARTICLES
        # -------------------------------------

        logger.info("Extracting article content.")

        articles = batch_fetch(urls, max_articles=2)

        if not articles:
            return jsonify({
                "success": False,
                "error": "Could not extract article content from the search results."
            }), 500

        # -------------------------------------
        # STEP 3: SUMMARIZE
        # -------------------------------------

        logger.info("Generating the research report.")

        result = summarize_research(topic, articles)

        if result.get("model_used") == "error":
            return jsonify({
                "success": False,
                "error": result.get("report", "AI summarization failed.")
            }), 500

        # -------------------------------------
        # FORMAT SOURCES
        # -------------------------------------

        sources = []

        for article in articles:
            url = article.get("url", "")

            if not url:
                continue

            sources.append({
                "title": article.get("title", "Untitled Source"),
                "url": url,
            })

        # -------------------------------------
        # SAVE HISTORY
        # -------------------------------------

        save_search_history(
            topic,
            result.get("report", ""),
            sources
        )

        # -------------------------------------
        # RESPONSE
        # -------------------------------------

        return jsonify({
            "success": True,
            "topic": topic,
            "report": result.get("report", "No report generated."),
            "model_used": result.get("model_used", "phi3"),
            "tokens_used": result.get("tokens_used", 0),
            "sources_analyzed": len(sources),
            "sources": sources,
        })

    except Exception as error:
        logger.exception("Research error")

        return jsonify({
            "success": False,
            "error": str(error),
        }), 500


# =========================================
# GET HISTORY
# =========================================

@app.route("/history", methods=["GET"])
def get_history():

    with history_lock:
        history = read_search_history()

    # Newest searches first.
    return jsonify(history[::-1])


# =========================================
# DELETE HISTORY ITEM
# =========================================

@app.route("/history/<int:index>", methods=["DELETE"])
def delete_history(index):

    with history_lock:
        history = read_search_history()

        # The frontend displays newest items first.
        if index < 0 or index >= len(history):
            return jsonify({
                "success": False,
                "error": "Search history item not found."
            }), 404

        actual_index = len(history) - 1 - index

        history.pop(actual_index)
        write_search_history(history)

    return jsonify({
        "success": True
    })


# =========================================
# HEALTH CHECK
# =========================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )

