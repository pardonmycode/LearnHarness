"""Limits shared by the editor and the requests to the learning server."""

from __future__ import annotations

# Characters of the open script the helper sees. A longer script is never replaced by
# generated code, because that code could only contain the part the helper has seen.
MAX_FILE_CONTEXT = 16_000
