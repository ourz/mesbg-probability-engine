from __future__ import annotations

from fractions import Fraction

from .schema import BranchSpec, StrikeSpec, WoundRollSpec
from .util import convolve_distributions
from .wound import solve_wound_roll, standard_wound_target


def _strike_damage_distribution(strike: StrikeSpec, defence: int) -> dict[int, Fraction]:
    target = strike.explicit_target
    if target is None:
        assert strike.strength is not None
        target = standard_wound_target(strike.strength, defence)
    if target is None:
        return {0: Fraction(1)}
    outcome = solve_wound_roll(
        WoundRollSpec(
            target=target,
            modifier=strike.modifier,
            reroll_rules=strike.reroll_rules,
            might_points=strike.might_points_per_roll,
            might_policy=strike.might_policy,
        )
    )
    distribution: dict[int, Fraction] = {0: 1 - outcome.success_probability}
    for damage, probability in strike.damage_distribution.items():
        distribution[damage] = distribution.get(damage, Fraction(0)) + outcome.success_probability * probability
    return distribution


def _fate_success_probability(target: int, reroll_failures: bool) -> Fraction:
    base = Fraction(7 - target, 6)
    if not reroll_failures:
        return base
    return base + (1 - base) * base


def _fate_event_outcomes(
    damage: int, fate_remaining: int, fate_success: Fraction
) -> dict[tuple[int, int], Fraction]:
    """Return (damage_applied, fate_left) after spending until prevented or empty."""
    if damage == 0 or fate_remaining <= 0:
        return {(damage, fate_remaining): Fraction(1)}
    outcomes: dict[tuple[int, int], Fraction] = {}
    failure_probability = Fraction(1)
    for attempts in range(1, fate_remaining + 1):
        success_probability = failure_probability * fate_success
        remaining = fate_remaining - attempts
        key = (0, remaining)
        outcomes[key] = outcomes.get(key, Fraction(0)) + success_probability
        failure_probability *= 1 - fate_success
    key = (damage, 0)
    outcomes[key] = outcomes.get(key, Fraction(0)) + failure_probability
    return outcomes


def _apply_fate_and_wounds(
    event_distribution: dict[tuple[int, int], Fraction],
    damage_distribution: dict[int, Fraction],
    fate_points: int,
    fate_target: int,
    fate_reroll_failures: bool,
    fate_policy: str,
) -> dict[tuple[int, int], Fraction]:
    del fate_points  # state carries the remaining resource exactly
    next_distribution: dict[tuple[int, int], Fraction] = {}
    fate_success = _fate_success_probability(fate_target, fate_reroll_failures)
    for (damage_so_far, fate_remaining), state_probability in event_distribution.items():
        for damage, damage_probability in damage_distribution.items():
            probability = state_probability * damage_probability
            if damage == 0 or fate_policy == "never" or fate_remaining <= 0:
                key = (damage_so_far + damage, fate_remaining)
                next_distribution[key] = next_distribution.get(key, Fraction(0)) + probability
                continue
            for (applied, remaining), fate_probability in _fate_event_outcomes(
                damage, fate_remaining, fate_success
            ).items():
                key = (damage_so_far + applied, remaining)
                next_distribution[key] = next_distribution.get(key, Fraction(0)) + probability * fate_probability
    return next_distribution


def solve_branch(branch: BranchSpec) -> dict[str, object]:
    roll_multiplier = 2 if branch.target.trapped or branch.target.prone else 1
    event_distributions: list[dict[int, Fraction]] = []
    for strike in branch.strikes:
        one = _strike_damage_distribution(strike, branch.target.defence)
        for _ in range(strike.count * roll_multiplier):
            event_distributions.append(one)

    states: dict[tuple[int, int], Fraction] = {
        (0, branch.target.fate.points): Fraction(1)
    }
    for event in event_distributions:
        states = _apply_fate_and_wounds(
            states,
            event,
            branch.target.fate.points,
            branch.target.fate.target,
            branch.target.fate.reroll_failures,
            branch.target.fate.policy,
        )

    damage_distribution: dict[int, Fraction] = {}
    for (damage, _fate_remaining), probability in states.items():
        damage_distribution[damage] = damage_distribution.get(damage, Fraction(0)) + probability
    expected_damage = sum(
        Fraction(damage) * probability for damage, probability in damage_distribution.items()
    )
    kill_probability = sum(
        probability
        for damage, probability in damage_distribution.items()
        if damage >= branch.target.wounds
    )
    at_least_one = 1 - damage_distribution.get(0, Fraction(0))
    return {
        "roll_multiplier": roll_multiplier,
        "damage_distribution": damage_distribution,
        "expected_damage": expected_damage,
        "at_least_one_wound_probability": at_least_one,
        "kill_probability": kill_probability,
    }
