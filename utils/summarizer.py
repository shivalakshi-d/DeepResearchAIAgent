"""
Ollama Cloud text summarization and image analysis.
"""

import logging
import os
import ollama

logger = logging.getLogger(__name__)

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma4:cloud")

# Connect to Ollama Cloud when an API key is configured.
if OLLAMA_API_KEY:
    client = ollama.Client(
        host="https://ollama.com",
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}"
        },
    )
else:
    # Local development fallback.
    client = ollama.Client()
    MODEL_NAME = os.getenv("OLLAMA_MODEL", "phi3")


def summarize_research(topic, articles):
    try:
        content = ""

        for index, article in enumerate(articles[:2], start=1):
            text = article.get("content", "")[:500]

            if text:
                content += f"\nSOURCE {index}:\n{text}\n"

        prompt = f"""
You are a helpful research assistant.

Write a clear, concise research report about:
{topic}

Organize the report into:
1. Summary
2. Key Points
3. Conclusion

Use the supplied information and do not invent facts.

SOURCE MATERIAL:
{content}
"""

        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "num_predict": 350,
                "temperature": 0.3,
            },
        )

        report = response.get("response", "No report generated.")

        total_tokens = (
            response.get("eval_count", 0)
            + response.get("prompt_eval_count", 0)
        )

        return {
            "report": report,
            "model_used": MODEL_NAME,
            "tokens_used": total_tokens,
        }

    except Exception:
        logger.exception("Text summarization failed")

        return {
            "report": (
                "Text summarization failed. Please check the "
                "Ollama Cloud API key, model availability, and service logs."
            ),
            "model_used": "error",
            "tokens_used": 0,
        }


def analyze_image(topic, image_bytes):
    try:
        question = topic or "Describe this image in detail."

        prompt = f"""
You are a visual analysis assistant.

Analyze the supplied image carefully.

User's question:
{question}

Provide:
1. A description of what is visible.
2. Important objects, text, and details.
3. The likely purpose or meaning, if identifiable.
4. A clear conclusion.

If details are unclear, say so instead of guessing.
"""

        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            images=[image_bytes],
            options={
                "temperature": 0.3,
            },
        )

        report = response.get("response", "No image analysis generated.")

        total_tokens = (
            response.get("eval_count", 0)
            + response.get("prompt_eval_count", 0)
        )

        return {
            "report": report,
            "model_used": MODEL_NAME,
            "tokens_used": total_tokens,
        }

    except Exception:
        logger.exception("Image analysis failed")

        return {
            "report": (
                "Image analysis failed. Please check the Ollama Cloud "
                "API key, model availability, and service logs."
            ),
            "model_used": "error",
            "tokens_used": 0,
        }