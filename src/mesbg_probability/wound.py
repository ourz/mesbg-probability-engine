from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .errors import ValidationError
from .schema import RerollRule, WoundRollSpec
from .util import clamp_die

# Printed 2024 To Wound chart. Split entries are ordinary modified target rolls;
# "natural" is only required when a separate rule explicitly says natural.
_TO_WOUND_CHART: dict[int, tuple[str, ...]] = {
    1: ("4+", "5+", "5+", "6+", "6+", "6+/4+", "6+/5+", "6+/6+", "-", "-"),
    2: ("4+", "4+", "5+", "5+", "6+", "6+", "6+/4+", "6+/5+", "6+/6+", "-"),
    3: ("3+", "4+", "4+", "5+", "5+", "6+", "6+", "6+/4+", "6+/5+", "6+/6+"),
    4: ("3+", "3+", "4+", "4+", "5+", "5+", "6+", "6+", "6+/4+", "6+/5+"),
    5: ("3+", "3+", "3+", "4+", "4+", "5+", "5+", "6+", "6+", "6+/4+"),
    6: ("3+", "3+", "3+", "3+", "4+", "4+", "5+", "5+", "6+", "6+"),
    7: ("3+", "3+", "3+", "3+", "3+", "4+", "4+", "5+", "5+", "6+"),
    8: ("3+", "3+", "3+", "3+", "3+", "3+", "4+", "4+", "5+", "5+"),
    9: ("3+", "3+", "3+", "3+", "3+", "3+", "3+", "4+", "4+", "5+"),
    10: ("3+", "3+", "3+", "3+", "3+", "3+", "3+", "3+", "4+", "4+"),
}


@dataclass(frozen=True)
class WoundRollOutcome:
    success_probability: Fraction
    might_spend_distribution: dict[int, Fraction]


def parse_wound_target(text: str | int | Iterable[int]) -> tuple[int, ...]:
    if isinstance(text, int):
        target = (text,)
    elif isinstance(text, str):
        cleaned = text.replace("+", "")
        target = tuple(int(piece) for piece in cleaned.split("/"))
    else:
        target = tuple(int(value) for value in text)
    if not target or len(target) > 2 or any(value < 2 or value > 6 for value in target):
        raise ValidationError(f"Invalid wound target {text!r}")
    return target


def standard_wound_target(strength: int, defence: int) -> tuple[int, ...] | None:
    if strength not in _TO_WOUND_CHART:
        raise ValidationError("Standard chart supports Strength 1-10")
    if defence < 1 or defence > 10:
        raise ValidationError("Standard chart supports Defence 1-10")
    cell = _TO_WOUND_CHART[strength][defence - 1]
    if cell == "-":
        return None
    return parse_wound_target(cell)


def _stage_success(raw: int, target: int, modifier: int, carried_might: int = 0) -> bool:
    return clamp_die(raw + modifier + carried_might) >= target


def _apply_rerolls(
    raw: int,
    stage: int,
    target: int,
    modifier: int,
    carried_might: int,
    rules: tuple[RerollRule, ...],
) -> list[tuple[int, Fraction]]:
    states: dict[tuple[int, bool], Fraction] = {(raw, False): Fraction(1)}
    for rule in rules:
        next_states: dict[tuple[int, bool], Fraction] = {}
        for (current_raw, already_rerolled), probability in states.items():
            should_reroll = False
            if stage in rule.stages and not already_rerolled:
                if rule.mode == "always":
                    should_reroll = True
                elif rule.mode == "raw_values":
                    should_reroll = current_raw in rule.raw_values
                elif rule.mode == "failed":
                    should_reroll = not _stage_success(
                        current_raw, target, modifier, carried_might
                    )
            if should_reroll:
                for reroll in range(1, 7):
                    key = (reroll, True)
                    next_states[key] = next_states.get(key, Fraction(0)) + probability * Fraction(1, 6)
            else:
                key = (current_raw, already_rerolled)
                next_states[key] = next_states.get(key, Fraction(0)) + probability
        states = next_states
    collapsed: dict[int, Fraction] = {}
    for (current_raw, _rerolled), probability in states.items():
        collapsed[current_raw] = collapsed.get(current_raw, Fraction(0)) + probability
    return list(collapsed.items())


def _minimum_might_to_succeed(raw: int, target: int, modifier: int, max_points: int) -> int | None:
    current = clamp_die(raw + modifier)
    if current >= target:
        return 0
    needed = target - current
    if needed <= max_points and current + needed <= 6:
        return needed
    return None


def solve_wound_roll(spec: WoundRollSpec) -> WoundRollOutcome:
    if not spec.target:
        return WoundRollOutcome(Fraction(0), {0: Fraction(1)})
    success_by_spend: dict[int, Fraction] = {}
    failure_by_spend: dict[int, Fraction] = {}

    first_target = spec.target[0]
    second_target = spec.target[1] if len(spec.target) == 2 else None

    for initial_raw in range(1, 7):
        initial_probability = Fraction(1, 6)
        for first_raw, reroll_probability in _apply_rerolls(
            initial_raw, 1, first_target, spec.modifier, 0, spec.reroll_rules
        ):
            base_probability = initial_probability * reroll_probability
            if spec.might_policy == "minimum_to_success":
                first_might = _minimum_might_to_succeed(
                    first_raw, first_target, spec.modifier, spec.might_points
                )
            else:
                first_might = 0 if _stage_success(first_raw, first_target, spec.modifier) else None
            if first_might is None:
                failure_by_spend[0] = failure_by_spend.get(0, Fraction(0)) + base_probability
                continue
            if second_target is None:
                success_by_spend[first_might] = success_by_spend.get(first_might, Fraction(0)) + base_probability
                continue

            remaining = spec.might_points - first_might
            # Might spent on stage one carries to stage two without being spent again.
            for second_initial in range(1, 7):
                second_initial_probability = Fraction(1, 6)
                for second_raw, second_reroll_probability in _apply_rerolls(
                    second_initial,
                    2,
                    second_target,
                    spec.modifier,
                    first_might,
                    spec.reroll_rules,
                ):
                    probability = base_probability * second_initial_probability * second_reroll_probability
                    if _stage_success(
                        second_raw, second_target, spec.modifier, first_might
                    ):
                        success_by_spend[first_might] = success_by_spend.get(first_might, Fraction(0)) + probability
                        continue
                    if spec.might_policy == "minimum_to_success":
                        current = clamp_die(second_raw + spec.modifier + first_might)
                        extra = second_target - current
                        if 0 < extra <= remaining and current + extra <= 6:
                            total_spend = first_might + extra
                            success_by_spend[total_spend] = success_by_spend.get(total_spend, Fraction(0)) + probability
                            continue
                    failure_by_spend[first_might] = failure_by_spend.get(first_might, Fraction(0)) + probability

    success_probability = sum(success_by_spend.values(), Fraction(0))
    spend_distribution: dict[int, Fraction] = {}
    for spend, probability in success_by_spend.items():
        spend_distribution[spend] = spend_distribution.get(spend, Fraction(0)) + probability
    for spend, probability in failure_by_spend.items():
        spend_distribution[spend] = spend_distribution.get(spend, Fraction(0)) + probability
    total = sum(spend_distribution.values(), Fraction(0))
    if total != 1:
        raise AssertionError(f"Wound roll probabilities sum to {total}, expected 1")
    return WoundRollOutcome(success_probability, spend_distribution)
