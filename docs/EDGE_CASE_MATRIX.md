# Edge-Case Matrix

| Edge case | Handling | Regression |
|---|---|---|
| Dice modifiers exceed bounds | Final die result clamped to 1–6 | Covered indirectly in Duel/Wound code |
| Two-handed Duel penalty | Applied only to the user's die | `test_two_handed_natural_six_remains_six` |
| Natural Duel 6 with two-handed weapon | Raw 6 override remains final 6 | Same test |
| Support supplies higher Fight | Fight is retained per die and side uses maximum | Galadhrim examples and Duel baselines |
| Banner can reroll a support die | Pool reroll selects any eligible identified die | `test_banner_can_reroll_support_die` |
| Multiple banners | A pool resource count is explicit; normal banner input uses one | Schema and examples |
| Both sides have optional rerolls | Decision order is mandatory and materially affects results | `test_both_side_reroll_order_is_explicit_and_material` |
| Same physical die rerolled twice | Rerolled state blocks later reroll rules | `test_same_physical_stage_not_rerolled_twice` |
| Second reroll result is worse | Second result stands | Enumeration semantics |
| Split wound roll | Each stage rolled separately | `test_each_split_stage_can_be_rerolled` |
| Modifier on split roll | Modifier applies to both stages | `test_split_first_stage_is_modified_not_natural` |
| Standard `6+/X+` first stage | Modified target, not intrinsically natural | Same test |
| Might on split first stage | Spent amount carries to stage two | `test_might_on_first_stage_carries_to_second` |
| Rerolls on both split stages | Each stage may be rerolled once | `test_each_split_stage_can_be_rerolled` |
| Trapped target | Two wound rolls per Strike | `test_trapped_and_prone_do_not_stack` |
| Prone target | Treated as Trapped after losing | Same test |
| Trapped and Prone together | Logical OR; still two rolls, never four | Same test |
| Cavalry knockdown | Caller derives eligibility; branch sets `prone` | Cavalry example |
| Physical self-trap under cavalry | Does not add another multiplier | Cavalry example and non-stacking test |
| Multiple Wounds | Damage distribution compared with target Wounds | Damage engine |
| Multiple damage from one Strike | One successful Fate roll prevents the whole event | `test_one_fate_prevents_entire_multi_damage_strike` |
| Failed Fate with Fate remaining | Spend again under preserve-life policy | `test_fate_spends_again_after_failure` |
| Unwoundable chart cell | Returns zero wound probability | Standard chart parser |
| Equal Fight roll-off | Explicit probability input | `test_equal_fight_elven_tie_advantage` |
| Contested Duel Might on both sides | Rejected in v0.1 rather than guessed | Parser validation |
| Shared finite Might across several Strikes | Not automated; run fixed-policy sensitivity cases | Deliberate boundary |
| Geometry / Make Way | Not inferred; caller supplies Trapped state | Deliberate boundary |
| Natural-6 bespoke triggers | Not inferred unless translated to supported inputs | Deliberate boundary |
