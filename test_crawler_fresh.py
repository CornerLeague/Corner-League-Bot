#!/usr/bin/env python3
"""
Test script to run a fresh crawler instance with RSS-only configuration
"""

import asyncio
import logging
from libs.common.config import get_settings
from apps.workers.crawler_worker import CrawlerWorker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fresh_crawler():
    """Test a fresh crawler instance with RSS-only configuration"""
    
    settings = get_settings()
    worker_id = f"test-crawler-{int(asyncio.get_event_loop().time())}"
    
    # Create a fresh crawler worker
    worker = CrawlerWorker(worker_id, settings)
    
    try:
        await worker.initialize()
        
        # Test URL discovery
        logger.info("Testing URL discovery...")
        urls = await worker._get_crawl_urls()
        
        logger.info(f"Discovered {len(urls)} URLs total")
        
        # Show breakdown by source
        rss_urls = await worker._get_rss_urls()
        sitemap_urls = await worker._get_sitemap_urls()
        search_urls = await worker._get_search_discovery_urls()
        
        logger.info(f"RSS URLs: {len(rss_urls)}")
        logger.info(f"Sitemap URLs: {len(sitemap_urls)}")
        logger.info(f"Search URLs: {len(search_urls)}")
        
        if rss_urls:
            logger.info(f"Sample RSS URLs: {rss_urls[:3]}")
        
        if len(urls) > 0 and len(sitemap_urls) == 0:
            logger.info("✅ RSS-only configuration is working correctly!")
            return True
        else:
            logger.error(f"❌ Configuration issue: {len(sitemap_urls)} sitemap URLs found")
            return False
            
    except Exception as e:
        logger.error(f"Error testing crawler: {e}")
        return False
    finally:
        await worker._cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_fresh_crawler())
    if success:
        print("\n✅ Fresh crawler test PASSED")
    else:
        print("\n❌ Fresh crawler test FAILED")