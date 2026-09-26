"""Mega mini-game content banks (~100k+ lines)."""
from .rps_taunts import RPS_TAUNTS
from .guess_hints import GUESS_HINTS
from .roulette_lines import ROULETTE_LINES
from .trivia_mega import TRIVIA_MEGA
from .hangman_words import HANG_WORDS
from .bj_lines import BJ_LINES
from .game_achievements import ACHIEVEMENTS

__all__ = [
    "RPS_TAUNTS", "GUESS_HINTS", "ROULETTE_LINES", "TRIVIA_MEGA",
    "HANG_WORDS", "BJ_LINES", "ACHIEVEMENTS",
]
