from fractions import Fraction
import unittest

from mesbg_probability.schema import RerollRule, WoundRollSpec
from mesbg_probability.wound import solve_wound_roll, standard_wound_target


class WoundTests(unittest.TestCase):
    def test_standard_chart_cells(self):
        self.assertEqual(standard_wound_target(5, 5), (4,))
        self.assertEqual(standard_wound_target(5, 6), (5,))
        self.assertEqual(standard_wound_target(5, 7), (5,))
        self.assertEqual(standard_wound_target(5, 8), (6,))
        self.assertEqual(standard_wound_target(3, 8), (6, 4))

    def test_unwoundable_chart_cell(self):
        self.assertIsNone(standard_wound_target(1, 9))

    def test_positive_modifier_caps_at_six(self):
        outcome = solve_wound_roll(WoundRollSpec(target=(6,), modifier=10))
        self.assertEqual(outcome.success_probability, Fraction(1))

    def test_negative_modifier_caps_at_one(self):
        outcome = solve_wound_roll(WoundRollSpec(target=(2,), modifier=-10))
        self.assertEqual(outcome.success_probability, Fraction(0))

    def test_split_first_stage_is_modified_not_natural(self):
        outcome = solve_wound_roll(WoundRollSpec(target=(6, 4), modifier=1))
        # First stage succeeds on 5+, second on 3+.
        self.assertEqual(outcome.success_probability, Fraction(2, 9))

    def test_might_on_first_stage_carries_to_second(self):
        outcome = solve_wound_roll(
            WoundRollSpec(
                target=(6, 4),
                modifier=0,
                might_points=1,
                might_policy="minimum_to_success",
            )
        )
        self.assertEqual(outcome.success_probability, Fraction(2, 9))

    def test_each_split_stage_can_be_rerolled(self):
        reroll_failed = RerollRule(mode="failed", stages=frozenset({1, 2}))
        outcome = solve_wound_roll(
            WoundRollSpec(target=(6, 4), reroll_rules=(reroll_failed,))
        )
        self.assertEqual(outcome.success_probability, Fraction(11, 48))

    def test_same_physical_stage_not_rerolled_twice(self):
        reroll_ones = RerollRule(mode="raw_values", raw_values=frozenset({1}), stages=frozenset({1}))
        reroll_failed = RerollRule(mode="failed", stages=frozenset({1}))
        outcome = solve_wound_roll(
            WoundRollSpec(target=(6,), reroll_rules=(reroll_ones, reroll_failed))
        )
        # Initial 1 gets only one reroll; 2-5 get one failure reroll.
        self.assertEqual(outcome.success_probability, Fraction(11, 36))


if __name__ == "__main__":
    unittest.main()
