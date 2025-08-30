#!/usr/bin/env python3
"""
Test script to verify the updated crawler with RSS-only configuration.
"""

import asyncio
import logging

from libs.common.config import get_settings
from libs.ingestion.crawler import WebCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_updated_crawler():
    """Test the updated crawler with RSS-only configuration"""

    settings = get_settings()

    async with WebCrawler(settings) as crawler:
        # Test source config with both RSS and sitemap URLs
        source_config = {
            "rss_url": "https://bleacherreport.com/articles/feed",
            "sitemap_url": "https://www.si.com/sitemap.xml"  # This should be ignored
        }

        logger.info("Testing URL discovery with RSS and sitemap URLs...")
        discovered_urls = await crawler.discover_urls(source_config)

        logger.info(f"Total URLs discovered: {len(discovered_urls)}")

        if discovered_urls:
            logger.info(f"Sample URLs: {discovered_urls[:3]}")

            # Check if any URLs are from sitemap (should be none)
            sitemap_urls = [url for url in discovered_urls if "sitemap" in url.lower()]
            if sitemap_urls:
                logger.error(f"❌ Found {len(sitemap_urls)} sitemap URLs - sitemap discovery not properly disabled!")
                return False
            else:
                logger.info("✅ No sitemap URLs found - sitemap discovery properly disabled!")
                return True
        else:
            logger.warning("No URLs discovered")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_updated_crawler())
    if success:
        print("\n✅ Updated crawler test PASSED - RSS-only mode working correctly")
    else:
        print("\n❌ Updated crawler test FAILED")
