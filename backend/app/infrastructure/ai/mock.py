"""The mock provider: deterministic, rule-based suggestions from the score
breakdown itself. Zero network, zero randomness — the same resume always
yields the same suggestions, and every test in the suite runs on this
(the locked rule), enforced by conftest regardless of AI_PROVIDER.
"""

from app.infrastructure.ai.base import SuggestionResult

_MAX_PER_LIST = 5

# Per-dimension copy. Strengths fire at full marks; improvements at zero or
# under half. Wording references ONLY what the rubric actually measured —
# the mock cannot fabricate, because it has nothing but the breakdown.
_STRENGTH_LINES = {
    "contact": (
        "Contact details are complete - email, phone, and a profile link "
        "are easy to find."
    ),
    "sections": (
        "All five standard sections (Summary, Experience, Education, "
        "Skills, Projects) are present."
    ),
    "length": "The length is right in the recommended range for a resume.",
    "action_verbs": (
        "Bullets lead with strong, distinct action verbs - this reads "
        "like ownership."
    ),
    "quantification": "Achievements are quantified with real numbers throughout.",
}
_IMPROVEMENT_LINES = {
    "contact": (
        "Add complete contact details: a professional email, phone "
        "number, and a LinkedIn or GitHub link."
    ),
    "sections": (
        "Add the standard sections recruiters scan for: Summary, "
        "Experience, Education, Skills, and Projects."
    ),
    "length": (
        "Adjust the length - aim for roughly 250 to 1000 words, enough "
        "depth without padding."
    ),
    "action_verbs": (
        "Start bullet points with strong action verbs (led, built, "
        "automated, reduced) instead of descriptions."
    ),
    "quantification": (
        "Quantify achievements with numbers: percentages, user counts, "
        "time saved, revenue impact."
    ),
}


class MockAnalysisProvider:
    name = "mock"

    def suggest(self, *, resume_text: str, breakdown: dict) -> SuggestionResult:
        strengths: list[str] = []
        improvements: list[str] = []
        for dimension in breakdown.get("dimensions", []):
            name = dimension["name"]
            earned, maximum = dimension["earned"], dimension["max"]
            if earned >= maximum:
                strengths.append(_STRENGTH_LINES[name])
            elif earned == 0 or earned < maximum / 2:
                improvements.append(_IMPROVEMENT_LINES[name])

        # Honest fallbacks, not filler: the mock says exactly what it can.
        if not strengths:
            strengths.append(
                "You have a foundation to build on — the checklist below is ordered by impact."
            )
        if not improvements:
            improvements.append(
                "Strong resume. The next step is tailoring it to each job description you apply to."
            )

        return SuggestionResult(
            strengths=strengths[:_MAX_PER_LIST],
            improvements=improvements[:_MAX_PER_LIST],
        )
