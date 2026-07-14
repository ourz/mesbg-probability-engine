from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from .errors import ValidationError
from .util import as_fraction


@dataclass(frozen=True)
class DieSpec:
    id: str
    fight: int
    modifier: int = 0
    raw_overrides: dict[int, int] = field(default_factory=dict)
    reroll_raw_values: frozenset[int] = frozenset()


@dataclass(frozen=True)
class PoolReroll:
    id: str
    side: str
    count: int
    eligible_dice: frozenset[str] | None = None
    forbid_if_currently_winning: bool = False


@dataclass(frozen=True)
class MightDecision:
    id: str
    side: str
    points: int
    eligible_dice: frozenset[str]


@dataclass(frozen=True)
class DuelSpec:
    dice_a: tuple[DieSpec, ...]
    dice_b: tuple[DieSpec, ...]
    equal_fight_a_win_probability: Fraction
    reroll_order: tuple[PoolReroll, ...] = ()
    might_order: tuple[MightDecision, ...] = ()


@dataclass(frozen=True)
class RerollRule:
    mode: str
    raw_values: frozenset[int] = frozenset()
    stages: frozenset[int] = frozenset({1, 2})


@dataclass(frozen=True)
class WoundRollSpec:
    target: tuple[int, ...]
    modifier: int = 0
    reroll_rules: tuple[RerollRule, ...] = ()
    might_points: int = 0
    might_policy: str = "none"


@dataclass(frozen=True)
class StrikeSpec:
    id: str
    count: int
    strength: int | None
    explicit_target: tuple[int, ...] | None
    modifier: int
    reroll_rules: tuple[RerollRule, ...]
    might_points_per_roll: int
    might_policy: str
    damage_distribution: dict[int, Fraction]


@dataclass(frozen=True)
class FateSpec:
    points: int = 0
    target: int = 4
    reroll_failures: bool = False
    policy: str = "preserve_life"


@dataclass(frozen=True)
class TargetSpec:
    defence: int
    wounds: int
    trapped: bool = False
    prone: bool = False
    fate: FateSpec = FateSpec()


@dataclass(frozen=True)
class BranchSpec:
    strikes: tuple[StrikeSpec, ...]
    target: TargetSpec


@dataclass(frozen=True)
class CombatSpec:
    schema_version: str
    metadata: dict[str, Any]
    duel: DuelSpec
    if_a_wins: BranchSpec
    if_b_wins: BranchSpec


def _parse_die_rows(side: str, rows: list[dict[str, Any]]) -> tuple[DieSpec, ...]:
    dice: list[DieSpec] = []
    seen: set[str] = set()
    for row in rows:
        base_id = str(row["id"])
        count = int(row.get("count", 1))
        if count < 1:
            raise ValidationError(f"Die group {base_id!r} must have count >= 1")
        fight = int(row["fight"])
        if fight < 1:
            raise ValidationError(f"Fight must be positive for {base_id!r}")
        raw_overrides = {int(k): int(v) for k, v in row.get("raw_overrides", {}).items()}
        reroll_raw_values = frozenset(int(v) for v in row.get("reroll_raw_values", []))
        for index in range(count):
            die_id = base_id if count == 1 else f"{base_id}#{index + 1}"
            qualified = f"{side}:{die_id}"
            if qualified in seen:
                raise ValidationError(f"Duplicate die id {qualified!r}")
            seen.add(qualified)
            dice.append(
                DieSpec(
                    id=qualified,
                    fight=fight,
                    modifier=int(row.get("modifier", 0)),
                    raw_overrides=raw_overrides,
                    reroll_raw_values=reroll_raw_values,
                )
            )
    if not dice:
        raise ValidationError(f"Side {side} needs at least one Duel die")
    return tuple(dice)


def _expand_ids(side: str, ids: list[str] | str, all_dice: tuple[DieSpec, ...]) -> frozenset[str] | None:
    if ids == "*" or ids == ["*"]:
        return None
    expanded: set[str] = set()
    available = {die.id for die in all_dice}
    for raw in ids:
        prefix = f"{side}:{raw}"
        exact = prefix
        matching = {die_id for die_id in available if die_id == exact or die_id.startswith(exact + "#")}
        if not matching:
            raise ValidationError(f"Unknown eligible die id {raw!r} for side {side}")
        expanded.update(matching)
    return frozenset(expanded)


def _parse_rerolls(
    rows: list[dict[str, Any]], dice_a: tuple[DieSpec, ...], dice_b: tuple[DieSpec, ...]
) -> tuple[PoolReroll, ...]:
    resources: list[PoolReroll] = []
    for index, row in enumerate(rows):
        side = str(row["side"]).upper()
        if side not in {"A", "B"}:
            raise ValidationError("Pool reroll side must be A or B")
        dice = dice_a if side == "A" else dice_b
        eligible = _expand_ids(side, row.get("eligible_dice", "*"), dice)
        count = int(row.get("count", 1))
        if count < 1:
            raise ValidationError("Pool reroll count must be >= 1")
        resources.append(
            PoolReroll(
                id=str(row.get("id", f"reroll_{index + 1}")),
                side=side,
                count=count,
                eligible_dice=eligible,
                forbid_if_currently_winning=bool(row.get("forbid_if_currently_winning", False)),
            )
        )
    return tuple(resources)


def _parse_might(
    rows: list[dict[str, Any]], dice_a: tuple[DieSpec, ...], dice_b: tuple[DieSpec, ...]
) -> tuple[MightDecision, ...]:
    decisions: list[MightDecision] = []
    for index, row in enumerate(rows):
        side = str(row["side"]).upper()
        if side not in {"A", "B"}:
            raise ValidationError("Might decision side must be A or B")
        dice = dice_a if side == "A" else dice_b
        eligible = _expand_ids(side, row.get("eligible_dice", "*"), dice)
        if eligible is None:
            eligible = frozenset(die.id for die in dice)
        points = int(row.get("points", 0))
        if points < 0:
            raise ValidationError("Might points cannot be negative")
        decisions.append(
            MightDecision(
                id=str(row.get("id", f"might_{index + 1}")),
                side=side,
                points=points,
                eligible_dice=eligible,
            )
        )
    return tuple(decisions)


def _parse_reroll_rules(rows: list[dict[str, Any]]) -> tuple[RerollRule, ...]:
    parsed: list[RerollRule] = []
    for row in rows:
        mode = str(row["mode"])
        if mode not in {"failed", "raw_values", "always"}:
            raise ValidationError(f"Unsupported reroll mode {mode!r}")
        raw_values = frozenset(int(v) for v in row.get("raw_values", []))
        if mode == "raw_values" and not raw_values:
            raise ValidationError("raw_values reroll rule needs at least one raw value")
        stages = frozenset(int(v) for v in row.get("stages", [1, 2]))
        if not stages.issubset({1, 2}):
            raise ValidationError("Reroll stages may only contain 1 and/or 2")
        parsed.append(RerollRule(mode=mode, raw_values=raw_values, stages=stages))
    return tuple(parsed)


def _parse_damage_distribution(raw: Any) -> dict[int, Fraction]:
    if raw is None:
        return {1: Fraction(1)}
    if isinstance(raw, int):
        if raw < 0:
            raise ValidationError("Damage cannot be negative")
        return {raw: Fraction(1)}
    if not isinstance(raw, dict):
        raise ValidationError("damage_distribution must be an integer or object")
    parsed = {int(k): as_fraction(v) for k, v in raw.items()}
    if any(damage < 0 for damage in parsed):
        raise ValidationError("Damage cannot be negative")
    if sum(parsed.values(), Fraction(0)) != 1:
        raise ValidationError("damage_distribution probabilities must sum to 1")
    return parsed


def _parse_strikes(rows: list[dict[str, Any]]) -> tuple[StrikeSpec, ...]:
    strikes: list[StrikeSpec] = []
    for index, row in enumerate(rows):
        explicit = row.get("wound_target")
        explicit_target = None
        if explicit is not None:
            if isinstance(explicit, int):
                explicit_target = (int(explicit),)
            else:
                explicit_target = tuple(int(v) for v in explicit)
        strength = row.get("strength")
        if strength is None and explicit_target is None:
            raise ValidationError("Each strike needs strength or wound_target")
        if strength is not None:
            strength = int(strength)
        count = int(row.get("count", 1))
        if count < 0:
            raise ValidationError("Strike count cannot be negative")
        might_policy = str(row.get("might_policy", "none"))
        if might_policy not in {"none", "minimum_to_success"}:
            raise ValidationError(f"Unsupported wound Might policy {might_policy!r}")
        strikes.append(
            StrikeSpec(
                id=str(row.get("id", f"strike_{index + 1}")),
                count=count,
                strength=strength,
                explicit_target=explicit_target,
                modifier=int(row.get("modifier", 0)),
                reroll_rules=_parse_reroll_rules(row.get("reroll_rules", [])),
                might_points_per_roll=int(row.get("might_points_per_roll", 0)),
                might_policy=might_policy,
                damage_distribution=_parse_damage_distribution(row.get("damage_distribution")),
            )
        )
    return tuple(strikes)


def _parse_target(raw: dict[str, Any]) -> TargetSpec:
    fate_raw = raw.get("fate", {})
    fate = FateSpec(
        points=int(fate_raw.get("points", 0)),
        target=int(fate_raw.get("target", 4)),
        reroll_failures=bool(fate_raw.get("reroll_failures", False)),
        policy=str(fate_raw.get("policy", "preserve_life")),
    )
    if fate.points < 0:
        raise ValidationError("Fate points cannot be negative")
    if not 2 <= fate.target <= 6:
        raise ValidationError("Fate target must be between 2 and 6")
    if fate.policy not in {"preserve_life", "never"}:
        raise ValidationError("Unsupported Fate policy")
    target = TargetSpec(
        defence=int(raw["defence"]),
        wounds=int(raw.get("wounds", 1)),
        trapped=bool(raw.get("trapped", False)),
        prone=bool(raw.get("prone", False)),
        fate=fate,
    )
    if target.defence < 1:
        raise ValidationError("Defence must be positive")
    if target.wounds < 1:
        raise ValidationError("Wounds must be positive")
    return target


def parse_combat_spec(raw: dict[str, Any]) -> CombatSpec:
    schema_version = str(raw.get("schema_version", ""))
    if schema_version != "combat-input-v1":
        raise ValidationError("schema_version must be combat-input-v1")
    duel_raw = raw["duel"]
    dice_a = _parse_die_rows("A", duel_raw["side_a"]["dice"])
    dice_b = _parse_die_rows("B", duel_raw["side_b"]["dice"])
    duel = DuelSpec(
        dice_a=dice_a,
        dice_b=dice_b,
        equal_fight_a_win_probability=as_fraction(
            duel_raw.get("equal_fight_a_win_probability", "1/2")
        ),
        reroll_order=_parse_rerolls(duel_raw.get("reroll_order", []), dice_a, dice_b),
        might_order=_parse_might(duel_raw.get("might_order", []), dice_a, dice_b),
    )
    if not 0 <= duel.equal_fight_a_win_probability <= 1:
        raise ValidationError("Tie probability must be between 0 and 1")
    might_sides = {decision.side for decision in duel.might_order if decision.points > 0}
    if len(might_sides) > 1:
        raise ValidationError(
            "combat-input-v1 does not automate contested Duel Might on both sides; "
            "derive a fixed sequence externally or run separate sensitivity cases"
        )
    branches = raw["branches"]
    a_branch = branches["if_a_wins"]
    b_branch = branches["if_b_wins"]
    return CombatSpec(
        schema_version=schema_version,
        metadata=dict(raw.get("metadata", {})),
        duel=duel,
        if_a_wins=BranchSpec(
            strikes=_parse_strikes(a_branch.get("strikes", [])),
            target=_parse_target(a_branch["target"]),
        ),
        if_b_wins=BranchSpec(
            strikes=_parse_strikes(b_branch.get("strikes", [])),
            target=_parse_target(b_branch["target"]),
        ),
    )
