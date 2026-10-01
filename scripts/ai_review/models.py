"""Typed review data shared by policy, provider, and rendering layers."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewResult(str, Enum):
    PASS = "PASS"
    PASS_WITH_COMMENTS = "PASS_WITH_COMMENTS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    title: str
    file: str
    line: int
    rule: str
    problem: str
    impact: str
    suggested_fix: str


@dataclass
class Review:
    findings: list[Finding] = field(default_factory=list)
    files_reviewed: list[str] = field(default_factory=list)
    rules_consulted: list[str] = field(default_factory=list)
    provider_note: str = "Deterministic project-policy review completed."

    @property
    def result(self) -> ReviewResult:
        if any(item.severity in {Severity.CRITICAL, Severity.HIGH} for item in self.findings):
            return ReviewResult.BLOCKED
        if self.findings:
            return ReviewResult.PASS_WITH_COMMENTS
        return ReviewResult.PASS

    def count(self, severity: Severity) -> int:
        return sum(item.severity is severity for item in self.findings)
