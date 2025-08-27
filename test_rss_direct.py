#!/usr/bin/env python3
"""
Direct test of RSS feed parsing without the full crawler infrastructure.
"""

import asyncio
import aiohttp
import feedparser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rss_direct():
    """Test RSS feed parsing directly"""
    
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
                    
                    logger.info(f"Feed title: {getattr(feed.feed, 'title', 'No title')}")
                    logger.info(f"Number of entries: {len(feed.entries)}")
                    
                    if feed.entries:
                        for i, entry in enumerate(feed.entries[:3]):
                            logger.info(f"Entry {i+1}: {getattr(entry, 'title', 'No title')}")
                            logger.info(f"  Link: {getattr(entry, 'link', 'No link')}")
                        return True
                    else:
                        logger.warning("No entries found in RSS feed")
                        return False
                else:
                    logger.error(f"Failed to fetch RSS feed: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_rss_direct())
    if success:
        print("\n✅ RSS feed test PASSED")
    else:
        print("\n❌ RSS feed test FAILED")