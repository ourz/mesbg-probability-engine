# Project and Calculation Audit

## Scope

This audit covers the MESBG Tournament Assistant 2.0 architecture supplied on 14 July 2026, its mathematical workflow, the Galadhrim/Court Guard calculations in the current conversation, and the edge cases implemented by engine version 0.1.0.

## Architecture finding

The probability solver should remain external executable code rather than consume the project’s reserved twenty-fifth persistent knowledge-file slot. The knowledge project remains responsible for:

1. FAQ/errata-first retrieval;
2. complete official baselines;
3. formation and interaction resolution;
4. the decisive-input ledger;
5. tactical interpretation.

The engine is responsible for deterministic arithmetic over a locked input specification.

Recommended project integration: add a version-pinned tool manifest to the existing README and a short invocation step to `07_UNIFIED_WORKFLOWS.md`; do not add another permanent knowledge file.

## Source integrity defect found

`REF_01_Rules_Manual_2024.md` currently states in the structured `rolling_to_wound` record that split entries such as `6+/4+` require a **natural 6** on the first roll. That is inconsistent with:

- the printed operative wording, which says to “score a 6+”;
- the general Dice Modifiers rule;
- the rule allowing Might on To Wound rolls;
- the rule that Might spent on the first stage carries to the second;
- project regression R-E7, which correctly requires modifiers to apply to both stages.

Recommended repair:

- change the structured wording from “natural 6” to “a modified result of 6+”;
- remove the same natural-6 assertion from the legacy To Wound chart note;
- add a regression asserting that `6+/4+` with `+1` succeeds on raw `5+`, then raw `3+`;
- add a regression asserting first-stage Might carryover.

The engine implements the printed modified-target interpretation.

## Conversation calculation audit

The numerical Galadhrim tables were recomputed from exact enumeration. Despite the later incorrect verbal claim about a natural first-stage 6, the previously reported D8 numbers were already calculated using modifiers on both split stages and are reproduced by the engine.

### Duel probabilities versus two lower-Fight dice

| Formation | No banner | Side A banner |
|---|---:|---:|
| Two ranks, normal front | 61.0340% | 71.9264% |
| Two ranks, two-handed front | 55.6327% | 68.9686% |
| Three ranks, normal front | 71.9264% | 78.9330% |
| Three ranks, two-handed front | 68.9686% | 77.2012% |

These reproduce the prior rounded values.

### Conditional kill probability after winning

| Defence | Two ranks | Two ranks, 2H front | Three ranks | Three ranks, 2H front |
|---|---:|---:|---:|---:|
| D4–5 | 75.0000% | 83.3333% | 87.5000% | 91.6667% |
| D6–7 | 55.5556% | 66.6667% | 70.3704% | 77.7778% |
| D8 | 39.5062% | 54.6296% | 52.9492% | 64.7119% |

### Kill probability per Combat

| Defence | Two ranks | Two ranks, 2H front | Three ranks | Three ranks, 2H front |
|---|---:|---:|---:|---:|
| D4–5 | 45.7755% | 46.3606% | 62.9356% | 63.2212% |
| D6–7 | 33.9078% | 37.0885% | 50.6149% | 53.6423% |
| D8 | 24.1122% | 30.3919% | 38.0845% | 44.6309% |

### Front-model death risk versus two enemy Strikes

The conditional kill chance after losing rises when physically trapped, but the third Duel die lowers how often that losing branch is reached.

| Enemy Strength | Two ranks, not trapped | Three ranks, trapped |
|---|---:|---:|
| S3 | 11.9063% | 14.5350% |
| S4–5 | 21.6478% | 22.5282% |
| S6 | 29.2245% | 26.3190% |

For a qualifying cavalry charge, the loser becomes Prone and is therefore already treated as Trapped. Physical trapping does not create a second doubling. Three ranks then reduce immediate casualty risk solely by improving the Duel-win probability.

## Calculation design audit

### Correct separations

The output keeps distinct:

- Duel-win probability;
- conditional damage after winning;
- expected damage per Combat;
- conditional kill probability;
- kill probability per Combat;
- defensive branch risk;
- complete damage distribution.

This matches the project’s Mathematical Verification Gate and avoids combining incompatible outputs into one efficiency score.

### Exact rather than sampled

All supported calculations enumerate the finite state space with rational arithmetic. There is no Monte Carlo noise, random seed or confidence interval.

### Input invalidation

Every output contains a canonical input SHA-256. Any change to a profile, rule, modifier, formation assumption, reroll order or target state changes the hash and requires a complete recalculation.

## Release assessment

Version 0.1.0 is suitable for public release as an audited arithmetic engine, subject to the deliberate boundaries listed in the README. It should not be represented as a rules database or geometry engine.
