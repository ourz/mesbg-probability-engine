"""Exact MESBG combat probability tools."""

from .engine import solve_combat
from .wound import parse_wound_target, standard_wound_target

__all__ = ["solve_combat", "parse_wound_target", "standard_wound_target"]
__version__ = "0.1.0"
