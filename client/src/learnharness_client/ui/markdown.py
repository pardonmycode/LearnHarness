"""Safe Markdown for tutor answers: formatting yes, links, images and HTML no."""

from __future__ import annotations

import re

from PyQt6.QtGui import QTextCursor, QTextDocument

_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_AUTOLINK = re.compile(r"<((?:https?|ftp|file|mailto):[^>\s]*)>", re.IGNORECASE)
_REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*\S+.*$", re.MULTILINE)
_REFERENCE_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")

# CommonMark without raw HTML: no bare-URL autolinks, tags stay visible as plain text.
MARKDOWN_FEATURES = QTextDocument.MarkdownFeature.MarkdownNoHTML


def sanitize_markdown(text: str) -> str:
    """Remove everything that could lead outside the app; keep code blocks untouched."""
    parts = re.split(r"(```.*?(?:```|$)|~~~.*?(?:~~~|$))", text, flags=re.DOTALL)
    cleaned: list[str] = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            cleaned.append(part)
            continue
        part = _IMAGE.sub(lambda match: match.group(1), part)
        part = _LINK.sub(lambda match: match.group(1), part)
        part = _REFERENCE_LINK.sub(lambda match: match.group(1), part)
        part = _AUTOLINK.sub(lambda match: match.group(1), part)
        part = _REFERENCE.sub("", part)
        cleaned.append(part)
    return "".join(cleaned)


def insert_markdown(cursor: QTextCursor, text: str) -> None:
    cursor.insertMarkdown(sanitize_markdown(text), MARKDOWN_FEATURES)


def has_links(document: QTextDocument) -> bool:
    """Used by tests: a sanitized tutor document must not contain any anchors."""
    return "href=" in document.toHtml()
