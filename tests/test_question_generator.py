import json
from types import SimpleNamespace

import httpx
import pytest
from google.genai._gaos.lib.compat_errors import BadRequestError

from ai_questions import QUESTION_GENERATION_RULES, build_question_prompt
from question_generator import QuestionGenerationError, generate_questions


def valid_questions(count):
    return [
        {
            "question": f"Question {index}",
            "options": [f"Option {letter}" for letter in "ABCD"],
            "correct": "A",
        }
        for index in range(count)
    ]


def test_ai_question_prompt_includes_rules_and_requested_category():
    prompt = build_question_prompt(5, "Science")

    assert QUESTION_GENERATION_RULES in prompt
    assert "exactly 5" in prompt
    assert "'Science'" in prompt
    assert "four distinct" in prompt
    assert "age-appropriate" in prompt


def test_generate_questions_uses_default_interactions_model_and_schema(monkeypatch):
    questions = valid_questions(5)
    request = {}

    class FakeInteractions:
        def create(self, **kwargs):
            request.update(kwargs)
            return SimpleNamespace(
                output_text=json.dumps({"questions": questions})
            )

    monkeypatch.setattr(
        "google.genai.Client",
        lambda api_key, http_options: SimpleNamespace(
            interactions=FakeInteractions()
        ),
    )

    assert generate_questions("test-key", 5) == questions
    assert request["model"] == "gemini-3.5-flash-lite"
    assert request["response_format"]["mime_type"] == "application/json"
    assert request["response_format"]["schema"]["properties"]["questions"][
        "minItems"
    ] == 5
    assert "General Knowledge" in request["input"]


def test_generate_questions_uses_model_from_environment(monkeypatch):
    request = {}

    class FakeInteractions:
        def create(self, **kwargs):
            request.update(kwargs)
            return SimpleNamespace(
                output_text=json.dumps({"questions": valid_questions(5)})
            )

    monkeypatch.setattr("google.genai.Client", lambda **kwargs: SimpleNamespace(
        interactions=FakeInteractions()
    ))
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")

    generate_questions("test-key", 5, "Science")

    assert request["model"] == "test-gemini-model"
    assert "Science" in request["input"]


def test_generate_questions_rejects_invalid_api_response(monkeypatch):
    questions = valid_questions(5)
    questions[0]["options"][1] = questions[0]["options"][0]

    class FakeInteractions:
        def create(self, **kwargs):
            return SimpleNamespace(
                output_text=json.dumps({"questions": questions})
            )

    monkeypatch.setattr(
        "google.genai.Client",
        lambda api_key, http_options: SimpleNamespace(
            interactions=FakeInteractions()
        ),
    )

    with pytest.raises(QuestionGenerationError, match="invalid format"):
        generate_questions("test-key", 5)


def test_generate_questions_reports_google_api_errors_and_redacts_key(
    monkeypatch, caplog
):
    api_key = "private-test-api-key"

    class FakeInteractions:
        def create(self, **kwargs):
            raise BadRequestError(
                f"invalid request using {api_key}",
                response=httpx.Response(
                    400, request=httpx.Request("POST", "https://example.test")
                ),
                body={"error": {"message": "invalid request"}},
            )

    monkeypatch.setattr(
        "google.genai.Client",
        lambda api_key, http_options: SimpleNamespace(
            interactions=FakeInteractions()
        ),
    )

    with pytest.raises(QuestionGenerationError, match="quiz_game.log"):
        generate_questions(api_key, 5)

    assert "Gemini request failed" in caplog.text
    assert "400" in caplog.text
    assert api_key not in caplog.text
