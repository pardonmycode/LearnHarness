"""Filters code out of text while it streams."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REPLACEMENT = (
    "\n(Hier hätte ich dir zu viel fertigen Code gezeigt. Probier es selbst – "
    "frag mich gern nach einem Tipp!)\n"
)


_CODE_LINE = re.compile(
    r"^\s*("
    r"func\s+\w+|var\s+\w+|const\s+\w+|extends\s+\w+|signal\s+\w+|@export|@onready|"
    r"(?:async\s+)?def\s+\w+|class\s+\w+.*:\s*$|import\s+\w+|from\s+[\w.]+\s+import\b|"
    r"try\s*:\s*$|except\b.*:\s*$|finally\s*:\s*$|with\s.+:\s*$|@\w+|"
    r"if\s.+:\s*$|elif\s.+:\s*$|else\s*:\s*$|for\s.+\sin\s.+:\s*$|while\s.+:\s*$|"
    r"match\s.+:\s*$|return\b|pass\s*$|"
    r"[A-Za-z_][\w.\[\]\"']*\s*([+\-*/]?=)\s*\S|"
    r"[A-Za-z_][\w.]*\(.*\)\s*$"
    r")"
)


def looks_like_code(line: str) -> bool:
    return bool(_CODE_LINE.match(line))


@dataclass
class StreamGuard:
    """Feed text pieces, get back what may be shown. Works line by line, so a long code block
    is never shown in part before it is recognised."""

    max_lines: int
    notes: list[str] = field(default_factory=list)
    _line: str = ""
    _fence: list[str] | None = None  # lines inside ``` … ```
    _loose: list[str] = field(default_factory=list)  # unfenced code-like lines

    def feed(self, text: str) -> str:
        out = []
        self._line += text
        while "\n" in self._line:
            line, self._line = self._line.split("\n", 1)
            out.append(self._take(line + "\n"))
        return "".join(out)

    def finish(self) -> str:
        out = self._take(self._line) if self._line else ""
        self._line = ""
        if self._fence is not None:
            out += self._close_fence(self._fence, closed=False)
            self._fence = None
        return out + self._flush_loose()

    def _take(self, line: str) -> str:
        stripped = line.strip()
        if self._fence is not None:
            if stripped.startswith("```"):
                block, self._fence = self._fence, None
                return self._close_fence(block, closed=True)
            self._fence.append(line)
            return ""
        if stripped.startswith("```"):
            pending = self._flush_loose()
            self._fence = [line]
            return pending
        if stripped and looks_like_code(line):
            self._loose.append(line)
            return ""
        if not stripped and self._loose:
            self._loose.append(line)  # blank line inside a code snippet
            return ""
        return self._flush_loose() + line

    def _close_fence(self, block: list[str], *, closed: bool) -> str:
        code = [line for line in block[1:] if line.strip()]
        if len(code) > self.max_lines:
            self.notes.append(f"Codeblock mit {len(code)} Zeilen ersetzt")
            return REPLACEMENT
        return "".join(block) + ("```\n" if closed else "\n```\n")

    def _flush_loose(self) -> str:
        lines, self._loose = self._loose, []
        code = [line for line in lines if line.strip()]
        if len(code) > self.max_lines:
            self.notes.append(f"Code ohne Codeblock ({len(code)} Zeilen) ersetzt")
            return REPLACEMENT
        return "".join(lines)


def filter_text(text: str, max_lines: int) -> tuple[str, list[str]]:
    guard = StreamGuard(max_lines)
    result = guard.feed(text) + guard.finish()
    return result, guard.notes
