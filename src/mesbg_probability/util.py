from __future__ import annotations

from fractions import Fraction
from typing import Any


def clamp_die(value: int) -> int:
    return max(1, min(6, value))


def as_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, float):
        return Fraction(str(value))
    if isinstance(value, str):
        text = value.strip()
        if "/" in text:
            numerator, denominator = text.split("/", 1)
            return Fraction(int(numerator), int(denominator))
        return Fraction(text)
    raise TypeError(f"Cannot convert {value!r} to Fraction")


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": f"{value.numerator}/{value.denominator}",
        "decimal": float(value),
        "percent": float(value * 100),
    }


def convolve_distributions(
    left: dict[int, Fraction], right: dict[int, Fraction]
) -> dict[int, Fraction]:
    result: dict[int, Fraction] = {}
    for left_value, left_probability in left.items():
        for right_value, right_probability in right.items():
            key = left_value + right_value
            result[key] = result.get(key, Fraction(0)) + left_probability * right_probability
    return result
