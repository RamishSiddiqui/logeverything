#!/usr/bin/env python3
"""
SOLUTION: Demonstrate the working fix for vertical line alignment.

The key insight is that emojis have inconsistent display widths in terminals.
The solution is to offer monospace symbols as an alternative.
"""

import logging
import os
import sys

# Add parent directory to path for importing logeverything
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from logeverything.handlers import PrettyFormatter


def demonstrate_solution():
    """Demonstrate the working solution for vertical line alignment."""

    print("=" * 80)
    print("SOLUTION: VERTICAL LINE ALIGNMENT FIX")
    print("=" * 80)
    print()

    print("PROBLEM: Emojis have inconsistent display widths")
    print("-" * 50)

    # Show the problem with emojis
    logger1 = logging.getLogger("EmojiProblem")
    logger1.setLevel(logging.DEBUG)
    logger1.handlers.clear()

    console_handler1 = logging.StreamHandler()

    # Original formatter with emojis
    emoji_formatter = PrettyFormatter(
        use_colors=False,
        use_symbols=True,
        use_indent=False,
        align_columns=True,
    )

    console_handler1.setFormatter(emoji_formatter)
    logger1.addHandler(console_handler1)

    print("With emojis (misaligned):")
    logger1.debug("│ Line should be straight")
    logger1.info("│ Line should be straight")
    logger1.warning("│ Line should be straight")
    logger1.error("│ Line should be straight")
    logger1.critical("│ Line should be straight")

    print()
    print("SOLUTION: Use monospace symbols")
    print("-" * 50)

    # Show the solution with monospace symbols
    logger2 = logging.getLogger("MonospaceSolution")
    logger2.setLevel(logging.DEBUG)
    logger2.handlers.clear()

    console_handler2 = logging.StreamHandler()

    # Custom formatter with monospace symbols
    class FixedFormatter(PrettyFormatter):
        LEVEL_SYMBOLS = {
            "DEBUG": "[D]",
            "INFO": "[I]",
            "WARNING": "[W]",
            "ERROR": "[E]",
            "CRITICAL": "[C]",
            "EXCEPTION": "[X]",
        }

    monospace_formatter = FixedFormatter(
        use_colors=False,
        use_symbols=True,
        use_indent=False,
        align_columns=True,
    )

    console_handler2.setFormatter(monospace_formatter)
    logger2.addHandler(console_handler2)

    print("With monospace symbols (perfectly aligned):")
    logger2.debug("│ Line should be straight")
    logger2.info("│ Line should be straight")
    logger2.warning("│ Line should be straight")
    logger2.error("│ Line should be straight")
    logger2.critical("│ Line should be straight")

    print()
    print("✅ SOLUTION SUMMARY:")
    print("1. The core alignment logic works correctly")
    print("2. Emojis have inconsistent terminal display widths")
    print("3. Monospace symbols ([D], [I], [W], [E], [C]) provide perfect alignment")
    print("4. The PrettyFormatter should offer both emoji and monospace options")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_solution()
