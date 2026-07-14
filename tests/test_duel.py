from fractions import Fraction
import unittest

from mesbg_probability.duel import solve_duel
from mesbg_probability.schema import DieSpec, DuelSpec, PoolReroll


class DuelTests(unittest.TestCase):
    def test_two_vs_two_superior_fight(self):
        a = (DieSpec("A:1", 6), DieSpec("A:2", 6))
        b = (DieSpec("B:1", 4), DieSpec("B:2", 4))
        result = solve_duel(DuelSpec(a, b, Fraction(1, 2)))
        self.assertEqual(result.a_win_probability, Fraction(791, 1296))

    def test_three_vs_two_superior_fight(self):
        a = tuple(DieSpec(f"A:{i}", 6) for i in range(3))
        b = tuple(DieSpec(f"B:{i}", 4) for i in range(2))
        result = solve_duel(DuelSpec(a, b, Fraction(1, 2)))
        self.assertEqual(result.a_win_probability, Fraction(5593, 7776))

    def test_equal_fight_elven_tie_advantage(self):
        a = tuple(DieSpec(f"A:{i}", 6) for i in range(2))
        b = tuple(DieSpec(f"B:{i}", 6) for i in range(2))
        result = solve_duel(DuelSpec(a, b, Fraction(2, 3)))
        self.assertEqual(result.a_win_probability, Fraction(2087, 3888))

    def test_two_handed_natural_six_remains_six(self):
        die = DieSpec("A:front", 5, modifier=-1, raw_overrides={6: 6})
        normal = DieSpec("B:enemy", 4)
        result = solve_duel(DuelSpec((die,), (normal,), Fraction(1, 2)))
        # Brute-known exact result for one two-handed die vs lower Fight one die.
        self.assertEqual(result.a_win_probability, Fraction(17, 36))

    def test_banner_can_reroll_support_die(self):
        a = (DieSpec("A:front", 5, modifier=-1, raw_overrides={6: 6}), DieSpec("A:support", 6))
        b = (DieSpec("B:1", 4), DieSpec("B:2", 4))
        banner = PoolReroll("banner", "A", 1, None, True)
        result = solve_duel(DuelSpec(a, b, Fraction(1, 2), (banner,), ()))
        # The exact solver may choose either eligible die after seeing the roll.
        self.assertGreater(result.a_win_probability, Fraction(5, 9))

    def test_both_side_reroll_order_is_explicit_and_material(self):
        a = (DieSpec("A:1", 5), DieSpec("A:2", 5))
        b = (DieSpec("B:1", 5), DieSpec("B:2", 5))
        a_banner = PoolReroll("a_banner", "A", 1, None, True)
        b_banner = PoolReroll("b_banner", "B", 1, None, True)
        first_a = solve_duel(DuelSpec(a, b, Fraction(1, 2), (a_banner, b_banner), ()))
        first_b = solve_duel(DuelSpec(a, b, Fraction(1, 2), (b_banner, a_banner), ()))
        self.assertNotEqual(first_a.a_win_probability, first_b.a_win_probability)


if __name__ == "__main__":
    unittest.main()
