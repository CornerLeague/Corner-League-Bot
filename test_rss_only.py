#!/usr/bin/env python3
"""
Test script to verify RSS feed discovery works with the comprehensive sports feeds list
"""

import asyncio
import logging
from libs.common.config import get_settings
from libs.ingestion.crawler import WebCrawler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rss_feeds():
    """Test RSS feed discovery with comprehensive sports feeds"""
    
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
        "https://www.foxsports.com/rss/sports",
        
        # League-specific feeds
        "https://www.nba.com/rss/nba_rss.xml",
        "https://www.nfl.com/feeds/rss/news",
        "https://www.mlb.com/feeds/news/rss.xml",
        "https://www.nhl.com/rss/news",
        
        # International sports
        "https://www.skysports.com/rss/12040",
        "https://www.goal.com/feeds/en/news",
        "https://www.eurosport.com/rss.xml",
        
        # College sports
        "https://www.ncaa.com/news/rss.xml",
        "https://www.collegeinsider.com/rss.php",
        
        # Fantasy and analysis
        "https://www.fantasypros.com/rss/news.xml",
        "https://www.rotowire.com/rss/news.htm"
    ]
    
    async with WebCrawler(settings) as crawler:
        total_urls = []
        
        for feed_url in rss_feeds[:5]:  # Test first 5 feeds
            try:
                logger.info(f"Testing RSS feed: {feed_url}")
                urls = await crawler.discovery_engine.discover_from_rss(feed_url)
                logger.info(f"Discovered {len(urls)} URLs from {feed_url}")
                
                if urls:
                    logger.info(f"Sample URLs: {urls[:3]}")
                    total_urls.extend(urls)
                else:
                    logger.warning(f"No URLs found in {feed_url}")
                    
            except Exception as e:
                logger.error(f"Failed to process {feed_url}: {e}")
                continue
        
        logger.info(f"Total URLs discovered: {len(total_urls)}")
        logger.info(f"Unique URLs: {len(set(total_urls))}")
        
        if total_urls:
            logger.info("RSS discovery is working correctly!")
            return True
        else:
            logger.error("No URLs discovered from any RSS feeds")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_rss_feeds())
    if success:
        print("\n✅ RSS feed discovery test PASSED")
    else:
        print("\n❌ RSS feed discovery test FAILED")