"""Gemini provider boundary tests (Phase 6 Step 3).

The conftest _force_mock_ai fixture keeps the service layer on the mock;
these tests exercise the Gemini class DIRECTLY with the SDK mocked —
prompt construction, response extraction, schema validation, and error
mapping. No test ever touches the network (locked rule).
"""

import pytest

from app.domain.exceptions import AiProviderError
from app.infrastructure.ai.gemini import (
    GeminiAnalysisProvider,
    _build_prompt,
    _parse_suggestions,
)

BREAKDOWN = {
    "version": "v1",
    "word_count": 300,
    "dimensions": [
        {"name": "contact", "earned": 15, "max": 15, "detail": "all"},
        {"name": "sections", "earned": 25, "max": 25, "detail": "all"},
    ],
}


def test_prompt_embeds_resume_text_and_forbids_scoring():
    prompt = _build_prompt("My resume text with Python experience", BREAKDOWN)

    assert "My resume text" in prompt
    assert "contact: 15/15" in prompt  # breakdown context included
    assert "do NOT score" in prompt  # anti-fabrication instruction present


def test_parse_accepts_valid_json():
    result = _parse_suggestions(
        '{"strengths": ["Clear skills"], "improvements": ["Add metrics"]}'
    )

    assert result.strengths == ["Clear skills"]
    assert result.improvements == ["Add metrics"]


def test_parse_strips_markdown_fencing():
    fenced = (
        "```json\n"
        '{"strengths": ["S"], "improvements": ["I"]}\n'
        "```"
    )
    result = _parse_suggestions(fenced)

    assert result.strengths == ["S"]


def test_parse_rejects_non_json_as_provider_error():
    with pytest.raises(AiProviderError):
        _parse_suggestions("I think this resume is pretty good!")


def test_parse_rejects_schema_violations_as_provider_error():
    # Missing improvements entirely:
    with pytest.raises(AiProviderError):
        _parse_suggestions('{"strengths": ["Only one side"]}')
    # Strengths present but empty:
    with pytest.raises(AiProviderError):
        _parse_suggestions('{"strengths": [], "improvements": ["x"]}')


def test_suggest_maps_sdk_errors_to_provider_error():
    provider = GeminiAnalysisProvider.__new__(GeminiAnalysisProvider)  # skip __init__
    provider._model = type("FakeModel", (), {})()

    def boom(_prompt):
        raise ConnectionError("network down")

    provider._model.generate_content = boom

    with pytest.raises(AiProviderError):
        provider.suggest(resume_text="text", breakdown=BREAKDOWN)


def test_suggest_happy_path_with_fake_model():
    provider = GeminiAnalysisProvider.__new__(GeminiAnalysisProvider)
    provider._model = type("FakeModel", (), {})()

    class FakeResponse:
        text = '{"strengths": ["Quantified"], "improvements": ["Add LinkedIn"]}'

    provider._model.generate_content = lambda _prompt: FakeResponse()

    result = provider.suggest(resume_text="text", breakdown=BREAKDOWN)

    assert result.strengths == ["Quantified"]
    assert result.improvements == ["Add LinkedIn"]
