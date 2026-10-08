"""The mock provider: deterministic, rule-based suggestions from the
breakdown itself. Zero network, zero randomness — and the ONLY provider
tests ever use (conftest enforces it)."""

from app.infrastructure.ai.base import SuggestionResult

_MAX_PER_LIST = 5

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

        if not strengths:
            strengths.append(
                "You have a foundation to build on - the improvements below "
                "are ordered by impact."
            )
        if not improvements:
            improvements.append(
                "Strong resume. The next step is tailoring it to each job "
                "description you apply to."
            )

        return SuggestionResult(
            strengths=strengths[:_MAX_PER_LIST],
            improvements=improvements[:_MAX_PER_LIST],
        )

    def suggest_match(
        self,
        *,
        resume_text: str,
        job_description: str,
        match_breakdown: dict,
        matched_keywords: list[str],
        missing_keywords: list[str],
    ) -> SuggestionResult:
        """Rule-based match text grounded in the REAL keyword lists (P7-6):
        references only the terms it was given, never invents others, never
        estimates a score."""
        strengths: list[str] = []
        improvements: list[str] = []

        if matched_keywords:
            top = ", ".join(matched_keywords[:5])
            strengths.append(f"Your resume already mentions: {top}.")
        if len(matched_keywords) >= 5:
            strengths.append(
                "Strong keyword overlap with this job description."
            )

        if missing_keywords:
            top = ", ".join(missing_keywords[:5])
            improvements.append(
                f"The description mentions terms your resume does not: {top}. "
                "Where you have real experience with them, add them with "
                "concrete outcomes."
            )
        if not strengths:
            strengths = ["No clear strengths surfaced for this pairing."]
        return SuggestionResult(
            strengths=strengths[:_MAX_PER_LIST],
            improvements=improvements[:_MAX_PER_LIST],
        )
