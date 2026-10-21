"""
Ollama text summarization and image analysis.
"""

import logging
import ollama

logger = logging.getLogger(__name__)


# =========================================
# TEXT RESEARCH SUMMARIZER
# =========================================

def summarize_research(topic, articles):

    try:
        content = ""

        for index, article in enumerate(articles[:2], start=1):
            text = article.get("content", "")[:500]

            if text:
                content += (
                    f"\nSOURCE {index}:\n"
                    f"{text}\n"
                )

        prompt = f"""
You are a helpful research assistant.

Write a clear, concise research report about:

{topic}

Use the supplied source information where available.

Organize the report using these sections:
1. Summary
2. Key Points
3. Conclusion

Be accurate. Do not invent facts or claim that you verified information
that is not present in the supplied source content.

SOURCE MATERIAL:
{content}
"""

        response = ollama.generate(
    model="phi3",
    prompt=prompt,
    options={
        "num_predict": 350,
        "temperature": 0.3
    }
)

        report = response.get(
            "response",
            "No report generated."
        )

        total_tokens = (
            response.get("eval_count", 0)
            + response.get("prompt_eval_count", 0)
        )

        return {
            "report": report,
            "model_used": "phi3",
            "tokens_used": total_tokens,
        }

    except Exception as error:
        logger.exception("Text summarization failed")

        return {
            "report": f"Text summarization failed: {error}",
            "model_used": "error",
            "tokens_used": 0,
        }


# =========================================
# IMAGE ANALYSIS USING LLAVA
# =========================================

def analyze_image(topic, image_bytes):

    try:
        question = topic or "Describe this image in detail."

        prompt = f"""
You are a visual analysis assistant.

Analyze the supplied image carefully.

User's question:
{question}

Please provide:
1. A description of what is visible.
2. Important objects, text, and details that can be identified.
3. An explanation of the image's purpose or meaning, if identifiable.
4. A clear conclusion.

If some details are unclear, say so instead of guessing.
Use simple, helpful language.
"""

        response = ollama.generate(
            model="llava",
            prompt=prompt,
            images=[image_bytes],
        )

        report = response.get(
            "response",
            "No image analysis generated."
        )

        total_tokens = (
            response.get("eval_count", 0)
            + response.get("prompt_eval_count", 0)
        )

        return {
            "report": report,
            "model_used": "llava",
            "tokens_used": total_tokens,
        }

    except Exception as error:
        logger.exception("Image analysis failed")

        return {
            "report": f"Image analysis failed: {error}",
            "model_used": "error",
            "tokens_used": 0,
        }
