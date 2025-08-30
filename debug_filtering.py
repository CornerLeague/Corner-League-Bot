#!/usr/bin/env python3


from libs.common.test_user_config import DODGERS_FILTER_CONFIG, TEST_USER_CONFIG


def debug_dodgers_relevant_content(title: str, text: str, keywords: list[str] = None) -> bool:
    """Debug version of is_dodgers_relevant_content to see what's matching."""
    content = f"{title} {text or ''}".lower()
    print(f"\nDebugging content: '{content[:100]}...'")

    # Check for team mentions
    team_aliases = [alias.lower() for alias in DODGERS_FILTER_CONFIG["team_aliases"]]
    for alias in team_aliases:
        if alias.lower() in content:
            print(f"✓ Found team alias: '{alias}'")
            return True
    print("✗ No team aliases found")

    # Check for stadium mention
    if DODGERS_FILTER_CONFIG["stadium"].lower() in content:
        print(f"✓ Found stadium: '{DODGERS_FILTER_CONFIG['stadium']}'")
        return True
    print("✗ No stadium mention found")

    # Check for specific Dodgers players or management
    dodgers_keywords = [kw.lower() for kw in TEST_USER_CONFIG["content_preferences"]["keywords"]]
    excluded_keywords = ["mlb", "national league", "nl west", "world series", "mlb playoffs"]

    for keyword in dodgers_keywords:
        if keyword.lower() in content and keyword.lower() not in excluded_keywords:
            print(f"✓ Found Dodgers keyword: '{keyword}'")
            return True
    print("✗ No specific Dodgers keywords found")

    # Check keywords if provided
    if keywords:
        content_keywords = [kw.lower() for kw in keywords if kw]
        test_keywords = [kw.lower() for kw in TEST_USER_CONFIG["content_preferences"]["keywords"]]

        for keyword in content_keywords:
            if any(test_kw in keyword or keyword in test_kw for test_kw in test_keywords):
                print(f"✓ Found matching provided keyword: '{keyword}'")
                return True
        print("✗ No matching provided keywords found")

    print("✗ Content not relevant to Dodgers")
    return False

if __name__ == "__main__":
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

    print("Debug Testing Content Relevance:")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        text = test_case["text"]
        expected = test_case["expected"]

        print(f"\nTest {i}: {title}...")
        result = debug_dodgers_relevant_content(title, text)

        status = "✓" if result == expected else "✗"
        print(f"{status} Result: {result} (expected: {expected})")

    print("\nDebug Testing Complete!")
