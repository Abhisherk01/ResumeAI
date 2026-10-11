"""PDF rendering via WeasyPrint (Phase 8, P8-1 + P8-5).

Infrastructure boundary, same doctrine as the parsing boundary: EVERY
library failure (missing system libs, font problems, internal renderer
errors) is converted to ONE domain error - PdfExportError - so resume
content or environment trouble can never produce a raw traceback or an
unhandled 500. PdfExportError is deliberately UNMAPPED in errors.py: the
fallthrough logs it (a server fault must be visible) and answers with the
standard 500 internal_error envelope.

WeasyPrint is imported lazily: the import is heavy and only the export
path needs it, so app startup and every non-export test skip the cost.
"""

import logging

from app.domain.exceptions import PdfExportError

logger = logging.getLogger(__name__)


def html_to_pdf(html: str) -> bytes:
    """Render one HTML string (the SAME output the preview endpoint
    serves) to PDF bytes."""
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf()
    except Exception as exc:
        logger.exception("PDF rendering failed")
        raise PdfExportError from exc
