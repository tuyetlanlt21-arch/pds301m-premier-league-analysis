"""Small unified-diff parser; it never executes code from a pull request."""

from dataclasses import dataclass, field
import re


@dataclass
class ChangedLine:
    number: int
    text: str


@dataclass
class FilePatch:
    path: str
    additions: list[ChangedLine] = field(default_factory=list)
    deleted: bool = False


def parse_unified_diff(diff: str) -> list[FilePatch]:
    """Return changed paths and added lines from a unified Git diff."""
    patches: list[FilePatch] = []
    current: FilePatch | None = None
    new_line = 0
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"diff --git a/(.+) b/(.+)$", line)
            if match:
                current = FilePatch(path=match.group(2))
                patches.append(current)
        elif current and line.startswith("deleted file mode"):
            current.deleted = True
        elif current and line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            new_line = int(match.group(1)) if match else 0
        elif current and line.startswith("+") and not line.startswith("+++"):
            current.additions.append(ChangedLine(new_line, line[1:]))
            new_line += 1
        elif current and not line.startswith("-") and not line.startswith("\\"):
            new_line += 1
    return patches
