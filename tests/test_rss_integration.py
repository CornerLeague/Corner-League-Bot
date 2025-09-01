#!/usr/bin/env python3
"""
Integrated RSS test suite.
Consolidates RSS testing for direct feed parsing and comprehensive feed discovery.
"""

import asyncio
import logging

import aiohttp
import feedparser

from libs.common.config import get_settings
from libs.ingestion.crawler import WebCrawler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rss_direct():
    """Test RSS feed parsing directly"""
    logger.info("Testing direct RSS feed parsing...")

    rss_url = "https://www.espn.com/espn/rss/news"

    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Fetching RSS feed: {rss_url}")
            async with session.get(rss_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"RSS content length: {len(content)} characters")

                    # Parse with feedparser
                    feed = feedparser.parse(content)

                    if feed.entries:
                        logger.info(f"Found {len(feed.entries)} entries in RSS feed")
                        logger.info(f"Feed title: {feed.feed.get('title', 'N/A')}")
                        logger.info(f"First entry title: {feed.entries[0].get('title', 'N/A')}")

                        logger.info("✅ Direct RSS test PASSED")
                        return True
                    else:
                        logger.error("❌ Direct RSS test FAILED - No entries found")
                        return False
                else:
                    logger.error(f"❌ Direct RSS test FAILED - HTTP {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Direct RSS test FAILED - Error: {e}")
            return False


async def test_rss_feeds_comprehensive():
    """Test RSS feed discovery with comprehensive sports feeds"""
    logger.info("Testing comprehensive RSS feed discovery...")

    settings = get_settings()

    # Comprehensive sports RSS feeds
    rss_feeds = [
        # Major sports news
        "http://rss.cnn.com/rss/edition_sport.rss",
        "https://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.espn.com/espn/rss/news",
        "https://www.si.com/rss/si_topstories.rss",
        "https://bleacherreport.com/articles/feed",
        "https://www.cbssports.com/rss/headlines/",
        "https://sports.yahoo.com/rss/",

        # NBA
        "https://www.espn.com/espn/rss/nba/news",
        "https://www.nba.com/rss/nba_rss.xml",

        # NFL
        "https://www.espn.com/espn/rss/nfl/news",
        "https://www.nfl.com/rss/rsslanding?searchString=home",

        # MLB
        "https://www.espn.com/espn/rss/mlb/news",
        "https://www.mlb.com/rss/news",

        # NHL
        "https://www.espn.com/espn/rss/nhl/news",
        "https://www.nhl.com/rss/news",

        # Soccer
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.mlssoccer.com/rss.xml",
    ]

    async with WebCrawler(settings) as crawler:
        successful_feeds = 0
        total_articles = 0

        for rss_url in rss_feeds[:5]:  # Test first 5 feeds to avoid timeout
            try:
                logger.info(f"Testing RSS feed: {rss_url}")

                # Test URL discovery from this RSS feed
                source_config = {"rss_url": rss_url}
                urls = await crawler.discover_urls_from_source(source_config)

                if urls:
                    successful_feeds += 1
                    total_articles += len(urls)
                    logger.info(f"✅ Found {len(urls)} articles from {rss_url}")
                else:
                    logger.warning(f"⚠️  No articles found from {rss_url}")

            except Exception as e:
                logger.warning(f"⚠️  Error processing {rss_url}: {e}")

        logger.info(f"\nRSS Feed Discovery Summary:")
        logger.info(f"Successful feeds: {successful_feeds}/{len(rss_feeds[:5])}")
        logger.info(f"Total articles discovered: {total_articles}")

        if successful_feeds >= 3:  # At least 3 out of 5 should work
            logger.info("✅ Comprehensive RSS test PASSED")
            return True
        else:
            logger.error("❌ Comprehensive RSS test FAILED - Too few successful feeds")
            return False


async def test_rss_feed_validation():
    """Test RSS feed validation and error handling"""
    logger.info("Testing RSS feed validation...")

    test_cases = [
        {
            "name": "Valid RSS feed",
            "url": "https://www.espn.com/espn/rss/news",
            "should_succeed": True
        },
        {
            "name": "Invalid RSS feed (404)",
            "url": "https://www.espn.com/nonexistent/rss/feed",
            "should_succeed": False
        },
        {
            "name": "Non-RSS URL",
            "url": "https://www.espn.com",
            "should_succeed": False
        }
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            try:
                logger.info(f"Testing: {test_case['name']}")

                async with session.get(
                    test_case['url'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)

                        has_entries = len(feed.entries) > 0
                        success = has_entries if test_case['should_succeed'] else not has_entries

                        if success:
                            logger.info(f"✅ {test_case['name']} - Expected result")
                            results.append(True)
                        else:
                            logger.error(f"❌ {test_case['name']} - Unexpected result")
                            results.append(False)
                    else:
                        # Non-200 status
                        success = not test_case['should_succeed']
                        if success:
                            logger.info(f"✅ {test_case['name']} - Expected failure (HTTP {response.status})")
                            results.append(True)
                        else:
                            logger.error(f"❌ {test_case['name']} - Unexpected failure (HTTP {response.status})")
                            results.append(False)

            except Exception as e:
                # Exception occurred
                success = not test_case['should_succeed']
                if success:
                    logger.info(f"✅ {test_case['name']} - Expected exception: {e}")
                    results.append(True)
                else:
                    logger.error(f"❌ {test_case['name']} - Unexpected exception: {e}")
                    results.append(False)

    passed = sum(results)
    total = len(results)

    if passed == total:
        logger.info("✅ RSS validation test PASSED")
        return True
    else:
        logger.error(f"❌ RSS validation test FAILED - {passed}/{total} passed")
        return False


async def run_all_rss_tests():
    """Run all RSS tests"""
    print("Running Integrated RSS Tests")
    print("=" * 35)
    print()

    results = []

    # Run individual tests
    logger.info("1. Testing direct RSS parsing...")
    results.append(await test_rss_direct())
    print()

    logger.info("2. Testing comprehensive RSS feed discovery...")
    results.append(await test_rss_feeds_comprehensive())
    print()

    logger.info("3. Testing RSS feed validation...")
    results.append(await test_rss_feed_validation())
    print()

    # Summary
    print("\nTest Summary:")
    print("=" * 20)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All RSS tests PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} RSS test(s) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_rss_tests())
    exit(0 if success else 1)
