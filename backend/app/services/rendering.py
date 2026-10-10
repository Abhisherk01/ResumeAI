"""HTML rendering for resume documents (Phase 8, P8-5 groundwork).

Security posture, stated so it is never relaxed casually:
- autoescape=True is the BOOLEAN, not select_autoescape: no template-file
  heuristic may ever leave user-authored resume text unescaped. A
  <script> pasted into a resume field MUST come out inert (tested).
- Templates render ONLY validated ResumeDocumentData - rendering never
  sees raw request bodies.
- The API's X-Frame-Options: DENY / CSP frame-ancestors 'none' stay in
  force: Step 4 embeds this HTML via a credentialed FETCH into a
  sandboxed srcdoc iframe, never by framing the API directly.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.schemas.resume_document import ResumeDocumentData

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_environment = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=True,  # the boolean - see module docstring
)


def render_document_html(
    data: ResumeDocumentData, *, template_id: str = "classic"
) -> str:
    """Render one document. Step 2 ships ONE draft template; until Step 3
    lands the four real ones, a stored template_id without a template file
    falls back to the draft - a valid save must never 500 on preview."""
    try:
        template = _environment.get_template(f"{template_id}.html.j2")
    except TemplateNotFound:
        template = _environment.get_template("resume_document.html.j2")
    return template.render(document=data)
