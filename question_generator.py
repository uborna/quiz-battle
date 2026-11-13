import json
import os
import re

from app_log import AppLog
from ai_questions import build_question_prompt

logger = AppLog.get("question_generator")


class QuestionGenerationError(Exception):
    pass


def generate_questions(
    api_key: str, count: int, category: str = "General Knowledge"
) -> list[dict[str, object]]:
    from google import genai
    from google.genai.errors import APIError
    from google.genai._gaos.lib.compat_errors import GeminiNextGenAPIClientError

    answer_letters = ["A", "B", "C", "D"]
    question_schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 4,
                            "maxItems": 4,
                        },
                        "correct": {
                            "type": "string",
                            "enum": answer_letters,
                        },
                    },
                    "required": ["question", "options", "correct"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["questions"],
        "additionalProperties": False,
    }
    prompt = build_question_prompt(count, category)
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    try:
        client = genai.Client(api_key=api_key, http_options={"timeout": 30000})
        interaction = client.interactions.create(
            model=model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": question_schema,
            },
        )
    except (APIError, GeminiNextGenAPIClientError) as error:
        detail = str(error).replace(api_key, "[REDACTED]")
        detail = re.sub(
            r"(?i)([?&]key=)[^&\s]+", r"\1[REDACTED]", detail
        )
        detail = re.sub(
            r"(?i)(authorization:\s*bearer\s+)[^\s,]+",
            r"\1[REDACTED]",
            detail,
        )
        status_code = getattr(error, "status_code", None)
        logger.error(
            "Gemini request failed (type=%s, status=%s): %s",
            type(error).__name__,
            status_code or "unavailable",
            detail,
        )
        raise QuestionGenerationError(
            "Google Gemini could not generate questions. Check your API key, "
            "internet connection, and AI Studio quota. See quiz_game.log for details."
        ) from error

    try:
        response = json.loads(interaction.output_text)
        questions = response["questions"]
        if not isinstance(questions, list) or len(questions) != count:
            raise ValueError("Unexpected number of generated questions.")
        for question in questions:
            if (
                not isinstance(question, dict)
                or not isinstance(question.get("question"), str)
                or not question["question"].strip()
                or not isinstance(question.get("options"), list)
                or len(question["options"]) != 4
                or any(
                    not isinstance(option, str) or not option.strip()
                    for option in question["options"]
                )
                or len({option.strip().casefold() for option in question["options"]}) != 4
                or question.get("correct") not in answer_letters
            ):
                raise ValueError("Generated question has an invalid format.")
        return questions
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        logger.error(
            "Gemini returned invalid question data (type=%s).",
            type(error).__name__,
        )
        raise QuestionGenerationError(
            "Google Gemini returned questions in an invalid format. Please try "
            "again. See quiz_game.log for details."
        ) from error
