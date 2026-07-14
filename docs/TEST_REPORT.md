# Test Report

Release candidate: `0.1.0`  
Test date: `2026-07-14`  
Python used for release validation: `3.13`

## Commands

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --no-build-isolation -w dist
python -m pip install --no-deps --no-build-isolation --target <temp> dist/*.whl
PYTHONPATH=<temp> python -m mesbg_probability validate \
  examples/galadhrim_two_rank_vs_infantry.json
```

## Result

- 21 unit and regression tests passed.
- All four example inputs solved successfully.
- The built wheel installed into a clean target directory.
- The installed CLI validated an example successfully.

## Covered regression groups

- superior-Fight and equal-Fight Duel probabilities;
- Elven tie advantage;
- two-handed natural 6 handling;
- support-die banner rerolls;
- both-side reroll order sensitivity;
- standard To Wound chart cells;
- modified split To Wound rolls;
- first-stage Might carryover;
- split-stage rerolls;
- one-reroll-per-physical-roll restriction;
- modifier caps;
- unwoundable cells;
- Trapped/Prone non-stacking;
- sequential Fate attempts;
- multi-damage Fate prevention;
- fail-closed input validation;
- rejection of contested both-side Duel Might in schema v1.
