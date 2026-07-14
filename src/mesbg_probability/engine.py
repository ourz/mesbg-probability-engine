from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Any

from .damage import solve_branch
from .duel import solve_duel
from .schema import parse_combat_spec
from .util import fraction_json


def _serialize_distribution(distribution: dict[int, Fraction]) -> dict[str, Any]:
    return {str(key): fraction_json(value) for key, value in sorted(distribution.items())}


def solve_combat(raw: dict[str, Any]) -> dict[str, Any]:
    spec = parse_combat_spec(raw)
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    input_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    duel = solve_duel(spec.duel)
    a_branch = solve_branch(spec.if_a_wins)
    b_branch = solve_branch(spec.if_b_wins)

    a_expected_per_combat = duel.a_win_probability * a_branch["expected_damage"]
    b_expected_per_combat = duel.b_win_probability * b_branch["expected_damage"]
    a_kill_per_combat = duel.a_win_probability * a_branch["kill_probability"]
    b_kill_per_combat = duel.b_win_probability * b_branch["kill_probability"]

    return {
        "schema_version": "combat-output-v1",
        "engine_version": "0.1.0",
        "input_sha256": input_sha256,
        "metadata": spec.metadata,
        "duel": {
            "side_a_win_probability": fraction_json(duel.a_win_probability),
            "side_b_win_probability": fraction_json(duel.b_win_probability),
        },
        "if_a_wins": {
            "wound_rolls_per_strike": a_branch["roll_multiplier"],
            "conditional_expected_damage": fraction_json(a_branch["expected_damage"]),
            "conditional_at_least_one_wound_probability": fraction_json(
                a_branch["at_least_one_wound_probability"]
            ),
            "conditional_kill_probability": fraction_json(a_branch["kill_probability"]),
            "damage_distribution": _serialize_distribution(a_branch["damage_distribution"]),
            "expected_damage_per_combat": fraction_json(a_expected_per_combat),
            "kill_probability_per_combat": fraction_json(a_kill_per_combat),
        },
        "if_b_wins": {
            "wound_rolls_per_strike": b_branch["roll_multiplier"],
            "conditional_expected_damage": fraction_json(b_branch["expected_damage"]),
            "conditional_at_least_one_wound_probability": fraction_json(
                b_branch["at_least_one_wound_probability"]
            ),
            "conditional_kill_probability": fraction_json(b_branch["kill_probability"]),
            "damage_distribution": _serialize_distribution(b_branch["damage_distribution"]),
            "expected_damage_per_combat": fraction_json(b_expected_per_combat),
            "kill_probability_per_combat": fraction_json(b_kill_per_combat),
        },
        "exchange": {
            "side_a_kills_target_probability": fraction_json(a_kill_per_combat),
            "side_b_kills_target_probability": fraction_json(b_kill_per_combat),
            "side_a_expected_damage": fraction_json(a_expected_per_combat),
            "side_b_expected_damage": fraction_json(b_expected_per_combat),
        },
    }
