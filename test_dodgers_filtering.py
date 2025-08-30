#!/usr/bin/env python3
"""
Test script to verify Dodgers content filtering functionality.
"""

import sys

sys.path.append(".")

from libs.common.test_user_config import (
    calculate_relevance_score,
    get_dodgers_filter_config,
    get_test_user_config,
    is_dodgers_relevant_content,
)


def test_dodgers_filtering():
    """Test the Dodgers content filtering functionality"""

    print("Testing Dodgers Content Filtering")
    print("=" * 40)

    # Get configurations
    user_config = get_test_user_config()
    dodgers_config = get_dodgers_filter_config()

    print(f"Test User Config: {user_config}")
    print(f"Dodgers Filter Config: {dodgers_config}")
    print()

    # Test cases
    test_cases = [
        {
            "title": "Dodgers Beat Giants 8-3 in Season Opener",
            "text": "Mookie Betts hit two home runs as the Los Angeles Dodgers defeated their rivals 8-3 at Dodger Stadium.",
            "expected": True
        },
        {
            "title": "Yankees Sign New Pitcher",
            "text": "The New York Yankees have signed a veteran pitcher to a multi-year contract.",
            "expected": False
        },
        {
            "title": "MLB Trade Deadline Approaches",
            "text": "Teams across baseball are making moves as the trade deadline nears. The Dodgers are rumored to be interested in several players.",
            "expected": True
        },
        {
            "title": "Basketball Season Preview",
            "text": "The NBA season is about to begin with several exciting matchups scheduled.",
            "expected": False
        }
    ]

    print("Testing Content Relevance:")
    print("-" * 30)

    for i, case in enumerate(test_cases, 1):
        title = case["title"]
        text = case["text"]
        expected = case["expected"]

        # Test relevance detection
        is_relevant = is_dodgers_relevant_content(title, text)
        relevance_score = calculate_relevance_score(title, text)

        status = "✓" if is_relevant == expected else "✗"

        print(f"{status} Test {i}: {title[:50]}...")
        print(f"   Relevant: {is_relevant} (expected: {expected})")
        print(f"   Score: {relevance_score:.2f}")
        print()

    print("Testing Complete!")

if __name__ == "__main__":
    test_dodgers_filtering()
