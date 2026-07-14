import json
from pathlib import Path
import unittest

from mesbg_probability.engine import solve_combat
from mesbg_probability.errors import ValidationError


ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    def test_example_solves_and_hashes(self):
        raw = json.loads((ROOT / "examples/galadhrim_three_rank_vs_infantry.json").read_text())
        result = solve_combat(raw)
        self.assertEqual(result["schema_version"], "combat-output-v1")
        self.assertEqual(len(result["input_sha256"]), 64)
        self.assertAlmostEqual(result["duel"]["side_a_win_probability"]["percent"], 71.9264403292)
        self.assertEqual(result["if_b_wins"]["wound_rolls_per_strike"], 2)


    def test_contested_duel_might_fails_closed(self):
        raw = json.loads((ROOT / "examples/galadhrim_three_rank_vs_infantry.json").read_text())
        raw["duel"]["might_order"] = [
            {"id": "a", "side": "A", "points": 1, "eligible_dice": ["front"]},
            {"id": "b", "side": "B", "points": 1, "eligible_dice": ["enemy"]}
        ]
        with self.assertRaises(ValidationError):
            solve_combat(raw)

    def test_unknown_schema_fails_closed(self):
        raw = json.loads((ROOT / "examples/galadhrim_three_rank_vs_infantry.json").read_text())
        raw["schema_version"] = "future-schema"
        with self.assertRaises(ValidationError):
            solve_combat(raw)


if __name__ == "__main__":
    unittest.main()
