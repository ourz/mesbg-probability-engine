from fractions import Fraction
import unittest

from mesbg_probability.damage import solve_branch
from mesbg_probability.schema import BranchSpec, FateSpec, StrikeSpec, TargetSpec


def strike(count=1, strength=3, modifier=0, damage=None):
    return StrikeSpec(
        id="strike",
        count=count,
        strength=strength,
        explicit_target=None,
        modifier=modifier,
        reroll_rules=(),
        might_points_per_roll=0,
        might_policy="none",
        damage_distribution=damage or {1: Fraction(1)},
    )


class DamageTests(unittest.TestCase):
    def test_trapped_and_prone_do_not_stack(self):
        trapped = solve_branch(
            BranchSpec((strike(count=2),), TargetSpec(defence=6, wounds=1, trapped=True))
        )
        both = solve_branch(
            BranchSpec((strike(count=2),), TargetSpec(defence=6, wounds=1, trapped=True, prone=True))
        )
        self.assertEqual(trapped["roll_multiplier"], 2)
        self.assertEqual(both["roll_multiplier"], 2)
        self.assertEqual(trapped["kill_probability"], both["kill_probability"])

    def test_untrapped_two_s3_strikes_vs_d6(self):
        result = solve_branch(
            BranchSpec((strike(count=2),), TargetSpec(defence=6, wounds=1))
        )
        self.assertEqual(result["kill_probability"], Fraction(11, 36))

    def test_fate_spends_again_after_failure(self):
        result = solve_branch(
            BranchSpec(
                (strike(count=1, strength=10),),
                TargetSpec(defence=1, wounds=1, fate=FateSpec(points=2, target=4)),
            )
        )
        # S10 vs D1 wounds on 3+: kill requires wound and both Fate attempts fail.
        self.assertEqual(result["kill_probability"], Fraction(2, 3) * Fraction(1, 4))

    def test_one_fate_prevents_entire_multi_damage_strike(self):
        result = solve_branch(
            BranchSpec(
                (strike(count=1, strength=10, damage={3: Fraction(1)}),),
                TargetSpec(defence=1, wounds=3, fate=FateSpec(points=1, target=4)),
            )
        )
        self.assertEqual(result["kill_probability"], Fraction(2, 3) * Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
