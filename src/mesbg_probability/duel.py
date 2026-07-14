from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from typing import Iterable

from .schema import DieSpec, DuelSpec, MightDecision, PoolReroll
from .util import clamp_die


@dataclass(frozen=True)
class DieState:
    id: str
    fight: int
    raw: int
    value: int
    rerolled: bool = False


@dataclass(frozen=True)
class DuelOutcome:
    a_win_probability: Fraction
    b_win_probability: Fraction


def _modified_value(spec: DieSpec, raw: int) -> int:
    if raw in spec.raw_overrides:
        return clamp_die(spec.raw_overrides[raw])
    return clamp_die(raw + spec.modifier)


def _die_distribution(spec: DieSpec) -> list[tuple[DieState, Fraction]]:
    outcomes: dict[DieState, Fraction] = {}
    for initial in range(1, 7):
        if initial in spec.reroll_raw_values:
            for reroll in range(1, 7):
                state = DieState(
                    id=spec.id,
                    fight=spec.fight,
                    raw=reroll,
                    value=_modified_value(spec, reroll),
                    rerolled=True,
                )
                outcomes[state] = outcomes.get(state, Fraction(0)) + Fraction(1, 36)
        else:
            state = DieState(
                id=spec.id,
                fight=spec.fight,
                raw=initial,
                value=_modified_value(spec, initial),
                rerolled=False,
            )
            outcomes[state] = outcomes.get(state, Fraction(0)) + Fraction(1, 6)
    return list(outcomes.items())


def _base_a_win_probability(
    dice_a: tuple[DieState, ...],
    dice_b: tuple[DieState, ...],
    equal_fight_a_win_probability: Fraction,
) -> Fraction:
    best_a = max(die.value for die in dice_a)
    best_b = max(die.value for die in dice_b)
    if best_a > best_b:
        return Fraction(1)
    if best_b > best_a:
        return Fraction(0)
    fight_a = max(die.fight for die in dice_a)
    fight_b = max(die.fight for die in dice_b)
    if fight_a > fight_b:
        return Fraction(1)
    if fight_b > fight_a:
        return Fraction(0)
    return equal_fight_a_win_probability


def _replace_dice(
    dice: tuple[DieState, ...], replacements: dict[int, DieState]
) -> tuple[DieState, ...]:
    return tuple(replacements.get(index, die) for index, die in enumerate(dice))


def _eligible_indices(
    resource: PoolReroll, dice: tuple[DieState, ...]
) -> list[int]:
    return [
        index
        for index, die in enumerate(dice)
        if not die.rerolled
        and (resource.eligible_dice is None or die.id in resource.eligible_dice)
    ]


def _reroll_subset_distribution(
    dice: tuple[DieState, ...], subset: tuple[int, ...], specs: dict[str, DieSpec]
) -> list[tuple[tuple[DieState, ...], Fraction]]:
    if not subset:
        return [(dice, Fraction(1))]
    result: list[tuple[tuple[DieState, ...], Fraction]] = []
    for raws in product(range(1, 7), repeat=len(subset)):
        replacements: dict[int, DieState] = {}
        for index, raw in zip(subset, raws, strict=True):
            old = dice[index]
            spec = specs[old.id]
            replacements[index] = DieState(
                id=old.id,
                fight=old.fight,
                raw=raw,
                value=_modified_value(spec, raw),
                rerolled=True,
            )
        result.append((_replace_dice(dice, replacements), Fraction(1, 6 ** len(subset))))
    return result


def _might_actions(
    decision: MightDecision, dice: tuple[DieState, ...]
) -> list[tuple[tuple[DieState, ...], int]]:
    eligible = [index for index, die in enumerate(dice) if die.id in decision.eligible_dice]
    actions: list[tuple[tuple[DieState, ...], int]] = [(dice, 0)]
    if decision.points <= 0 or not eligible:
        return actions

    increments: set[tuple[int, ...]] = set()

    def build(position: int, remaining: int, current: list[int]) -> None:
        if position == len(eligible):
            increments.add(tuple(current))
            return
        die = dice[eligible[position]]
        max_increment = min(6 - die.value, remaining)
        for amount in range(max_increment + 1):
            current.append(amount)
            build(position + 1, remaining - amount, current)
            current.pop()

    build(0, decision.points, [])
    for allocation in increments:
        spent = sum(allocation)
        if spent == 0:
            continue
        replacements: dict[int, DieState] = {}
        for index, amount in zip(eligible, allocation, strict=True):
            if amount:
                die = dice[index]
                replacements[index] = DieState(
                    id=die.id,
                    fight=die.fight,
                    raw=die.raw,
                    value=die.value + amount,
                    rerolled=die.rerolled,
                )
        actions.append((_replace_dice(dice, replacements), spent))
    return actions


def _solve_decisions(
    duel: DuelSpec,
    dice_a: tuple[DieState, ...],
    dice_b: tuple[DieState, ...],
    specs: dict[str, DieSpec],
    reroll_index: int,
    might_index: int,
) -> Fraction:
    if reroll_index < len(duel.reroll_order):
        resource = duel.reroll_order[reroll_index]
        owner_dice = dice_a if resource.side == "A" else dice_b
        current = _base_a_win_probability(
            dice_a, dice_b, duel.equal_fight_a_win_probability
        )
        if resource.forbid_if_currently_winning:
            owner_winning = current == 1 if resource.side == "A" else current == 0
            if owner_winning:
                return _solve_decisions(
                    duel, dice_a, dice_b, specs, reroll_index + 1, might_index
                )
        eligible = _eligible_indices(resource, owner_dice)
        subsets: list[tuple[int, ...]] = [()]
        for size in range(1, min(resource.count, len(eligible)) + 1):
            subsets.extend(combinations(eligible, size))
        action_values: list[Fraction] = []
        for subset in subsets:
            expected = Fraction(0)
            for rerolled, probability in _reroll_subset_distribution(owner_dice, subset, specs):
                next_a, next_b = (rerolled, dice_b) if resource.side == "A" else (dice_a, rerolled)
                expected += probability * _solve_decisions(
                    duel, next_a, next_b, specs, reroll_index + 1, might_index
                )
            action_values.append(expected)
        return max(action_values) if resource.side == "A" else min(action_values)

    if might_index < len(duel.might_order):
        decision = duel.might_order[might_index]
        owner_dice = dice_a if decision.side == "A" else dice_b
        action_values: list[Fraction] = []
        for adjusted, _spent in _might_actions(decision, owner_dice):
            next_a, next_b = (adjusted, dice_b) if decision.side == "A" else (dice_a, adjusted)
            action_values.append(
                _solve_decisions(
                    duel, next_a, next_b, specs, reroll_index, might_index + 1
                )
            )
        return max(action_values) if decision.side == "A" else min(action_values)

    return _base_a_win_probability(dice_a, dice_b, duel.equal_fight_a_win_probability)


def solve_duel(duel: DuelSpec) -> DuelOutcome:
    specs = {die.id: die for die in (*duel.dice_a, *duel.dice_b)}
    distributions_a = [_die_distribution(die) for die in duel.dice_a]
    distributions_b = [_die_distribution(die) for die in duel.dice_b]
    a_win = Fraction(0)
    for outcomes_a in product(*distributions_a):
        dice_a = tuple(state for state, _probability in outcomes_a)
        probability_a = _product_probability(probability for _state, probability in outcomes_a)
        for outcomes_b in product(*distributions_b):
            dice_b = tuple(state for state, _probability in outcomes_b)
            probability_b = _product_probability(probability for _state, probability in outcomes_b)
            conditional = _solve_decisions(duel, dice_a, dice_b, specs, 0, 0)
            a_win += probability_a * probability_b * conditional
    return DuelOutcome(a_win_probability=a_win, b_win_probability=1 - a_win)


def _product_probability(probabilities: Iterable[Fraction]) -> Fraction:
    result = Fraction(1)
    for probability in probabilities:
        result *= probability
    return result
