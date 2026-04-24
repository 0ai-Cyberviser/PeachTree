from __future__ import annotations

from dataclasses import dataclass, field
import re

from .models import SourceDocument

SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
    re.compile(r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
)

DEFAULT_ALLOWED_LICENSES = {
    "apache-2.0",
    "mit",
    "bsd-2-clause",
    "bsd-3-clause",
    "mpl-2.0",
    "unlicense",
    "cc0-1.0",
    "unknown",
}


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    score: float = 1.0


@dataclass
class SafetyGate:
    allowed_licenses: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_LICENSES))
    allow_unknown_license: bool = True
    max_document_chars: int = 80_000

    def check_document(self, doc: SourceDocument) -> SafetyDecision:
        if len(doc.content) > self.max_document_chars:
            return SafetyDecision(False, "document too large", 0.0)

        license_id = doc.license_id.lower()
        if license_id == "unknown" and not self.allow_unknown_license:
            return SafetyDecision(False, "unknown license rejected", 0.0)
        if license_id not in self.allowed_licenses:
            return SafetyDecision(False, f"license not allowlisted: {doc.license_id}", 0.0)

        for pattern in SECRET_PATTERNS:
            if pattern.search(doc.content):
                return SafetyDecision(False, "secret-like content detected", 0.0)

        if self._looks_like_private_data(doc.content):
            return SafetyDecision(False, "personal-data-like content detected", 0.2)

        return SafetyDecision(True, "allowed", 1.0)

    def sanitize(self, text: str) -> str:
        output = text
        for pattern in SECRET_PATTERNS:
            output = pattern.sub("[REDACTED_SECRET]", output)
        output = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", output)
        return output

    @staticmethod
    def _looks_like_private_data(text: str) -> bool:
        email_count = len(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
        return email_count > 5
