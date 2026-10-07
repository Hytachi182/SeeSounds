"""Free-text answer normalisation and matching."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from rapidfuzz.fuzz import ratio


def normalize_answer(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    without_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    without_punctuation = re.sub(r"[^\w\s]", " ", without_accents.casefold())
    return " ".join(without_punctuation.split())


@dataclass(frozen=True)
class MatchResult:
    normalized: str
    similarity: float
    result: str  # correct | almost | incorrect
    matched_against: str


def compare_answer(answer: str, expected: str, aliases: list[str], correct_threshold: int = 90,
                   almost_threshold: int = 75) -> MatchResult:
    normalized = normalize_answer(answer)
    candidates = [expected, *aliases]
    scores = [(candidate, float(ratio(normalized, normalize_answer(candidate)))) for candidate in candidates]
    matched, score = max(scores, key=lambda pair: pair[1])
    status = "correct" if score >= correct_threshold else "almost" if score >= almost_threshold else "incorrect"
    return MatchResult(normalized, score, status, matched)
