from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AtsDecision:
    should_answer: bool
    value: str | None
    confidence: float
    reason: str


def normalize_option_map(options: list[str]) -> dict[str, str]:
    """Mapea opción normalizada -> opción original.

    Normaliza: trim + lower + collapse spaces.
    """
    norm_map: dict[str, str] = {}
    for o in options:
        if o is None:
            continue
        n = " ".join(str(o).split()).strip().lower()
        if not n:
            continue
        # primer wins
        norm_map.setdefault(n, str(o))
    return norm_map


def validate_decision_against_options(*, should_answer: bool, value: str | None, confidence: float, reason: str, options: list[str]) -> AtsDecision:
    if not should_answer or value is None:
        return AtsDecision(should_answer=False, value=None, confidence=confidence, reason=reason)

    norm_map = normalize_option_map(options)
    v_norm = " ".join(str(value).split()).strip().lower()

    if v_norm in norm_map:
        return AtsDecision(should_answer=True, value=norm_map[v_norm], confidence=confidence, reason=reason)

    # Failsafe: NO interactuar si no pertenece estrictamente al set de options
    return AtsDecision(
        should_answer=False,
        value=None,
        confidence=confidence,
        reason=f"value_no_match_options (value='{value}')",
    )

