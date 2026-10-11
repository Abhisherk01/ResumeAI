"""HTML rendering for resume documents (Phase 8, P8-5).

Security posture, stated so it is never relaxed casually:
- autoescape=True is the BOOLEAN, not select_autoescape: no template-file
  heuristic may ever leave user-authored resume text unescaped. A
  <script> pasted into a resume field MUST come out inert (tested).
- Templates render ONLY validated ResumeDocumentData - rendering never
  sees raw request bodies.
- The API's X-Frame-Options: DENY / CSP frame-ancestors 'none' stay in
  force: Step 4 embeds this HTML via a credentialed FETCH into a
  sandboxed srcdoc iframe, never by framing the API directly.

Step 3: all four storable template ids (P8-5) have real files, so the
Step-2 fallback is GONE - an unknown id raises TemplateNotFound and fails
loudly. It cannot occur through the API: the save schema's Literal is the
boundary, and a loud failure beats silently rendering the wrong design.

The SAME rendered string feeds the preview endpoint and WeasyPrint
export - one visual source of truth.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.schemas.resume_document import ResumeDocumentData

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_environment = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=True,  # the boolean - see module docstring
)


def render_document_html(
    data: ResumeDocumentData, *, template_id: str, accent: str
) -> str:
    """Render one document with one accent palette. Both ids are stored
    columns, Literal-validated at every save (P8-4)."""
    template = _environment.get_template(f"{template_id}.html.j2")
    return template.render(document=data, accent=accent)
