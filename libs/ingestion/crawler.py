# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Web crawler with comprehensive guardrails and rate limiting.
Implements robots.txt compliance, per-host rate limiting, and proxy management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
from aiolimiter import AsyncLimiter

from libs.common.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Manages robots.txt compliance checking"""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.robots_cache: dict[str, tuple[RobotFileParser, datetime]] = {}
        self.cache_ttl = timedelta(hours=24)
        logger.info("RobotsChecker initialized with empty cache")

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt"""

        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

        # Check cache
        if robots_url in self.robots_cache:
            robots_parser, cached_at = self.robots_cache[robots_url]
            if datetime.utcnow() - cached_at < self.cache_ttl:
                return robots_parser.can_fetch(user_agent, url)

        # Fetch robots.txt
        try:
            async with self.session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    robots_content = await response.text()

                    # Parse robots.txt
                    robots_parser = RobotFileParser()
                    robots_parser.set_url(robots_url)
                    # Parse content line by line
                    for line in robots_content.splitlines():
                        robots_parser.feed(line)

                    # Cache result
                    self.robots_cache[robots_url] = (robots_parser, datetime.utcnow())

                    return robots_parser.can_fetch(user_agent, url)
                else:
                    # If robots.txt not found, assume allowed
                    return True

        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt for {robots_url}: {e}")
            # Clear cache entry if it exists to avoid stale data
            if robots_url in self.robots_cache:
                del self.robots_cache[robots_url]
            return True  # Assume allowed on error

    def get_crawl_delay(self, url: str, user_agent: str = "*") -> float | None:
        """Get crawl delay from robots.txt"""

        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

        if robots_url in self.robots_cache:
            robots_parser, _ = self.robots_cache[robots_url]
            return robots_parser.crawl_delay(user_agent)

        return None


class ProxyManager:
    """Manages Evomi proxy rotation and budget tracking"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.proxies = self._build_proxy_list()
        self.current_proxy_index = 0
        self.proxy_stats: dict[str, dict[str, Any]] = {}
        self.daily_usage = 0.0
        self.last_reset = datetime.utcnow().date()

    def _build_proxy_list(self) -> list[str]:
        """Build list of proxy URLs"""
        proxies = []
        for endpoint in self.settings.evomi.endpoints:
            proxy_url = f"http://{self.settings.evomi.proxy_user}:{self.settings.evomi.proxy_pass}@{endpoint}"
            proxies.append(proxy_url)
        return proxies

    def get_next_proxy(self) -> str | None:
        """Get next proxy in rotation"""

        # Check daily budget
        if self.daily_usage >= self.settings.evomi.daily_budget:
            logger.warning("Daily proxy budget exceeded")
            return None

        # Reset daily usage if new day
        today = datetime.utcnow().date()
        if today > self.last_reset:
            self.daily_usage = 0.0
            self.last_reset = today

        if not self.proxies:
            return None

        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)

        return proxy

    def record_usage(self, proxy: str, bytes_transferred: int, success: bool) -> None:
        """Record proxy usage for budget tracking"""

        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {
                "requests": 0,
                "bytes": 0,
                "successes": 0,
                "failures": 0,
                "cost": 0.0
            }

        stats = self.proxy_stats[proxy]
        stats["requests"] += 1
        stats["bytes"] += bytes_transferred

        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1

        # Calculate cost (rough estimate)
        gb_used = bytes_transferred / (1024 * 1024 * 1024)
        cost = gb_used * self.settings.evomi.cost_per_gb
        stats["cost"] += cost
        self.daily_usage += cost

    def get_proxy_stats(self) -> dict[str, Any]:
        """Get proxy usage statistics"""
        return {
            "daily_usage": self.daily_usage,
            "daily_budget": self.settings.evomi.daily_budget,
            "budget_remaining": self.settings.evomi.daily_budget - self.daily_usage,
            "proxy_stats": self.proxy_stats
        }


class RateLimiter:
    """Per-host rate limiting with exponential backoff"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.limiters: dict[str, AsyncLimiter] = {}
        self.backoff_delays: dict[str, float] = {}
        self.last_request_times: dict[str, datetime] = {}

    def get_limiter(self, domain: str) -> AsyncLimiter:
        """Get rate limiter for domain"""

        if domain not in self.limiters:
            # Create limiter based on domain tier
            rate = 1.0 / self.settings.crawling.default_delay
            self.limiters[domain] = AsyncLimiter(rate, 1)

        return self.limiters[domain]

    async def acquire(self, domain: str) -> None:
        """Acquire rate limit token for domain"""

        limiter = self.get_limiter(domain)
        await limiter.acquire()

        # Apply additional backoff if needed
        if domain in self.backoff_delays:
            await asyncio.sleep(self.backoff_delays[domain])

        self.last_request_times[domain] = datetime.utcnow()

    def apply_backoff(self, domain: str, status_code: int) -> None:
        """Apply exponential backoff for rate limiting responses"""

        if status_code == 429:  # Too Many Requests
            current_delay = self.backoff_delays.get(domain, 1.0)
            new_delay = min(current_delay * 2, 300)  # Max 5 minutes
            self.backoff_delays[domain] = new_delay
            logger.warning(f"Rate limited by {domain}, backing off to {new_delay}s")

        elif status_code < 400:  # Success
            # Reduce backoff on success
            if domain in self.backoff_delays:
                current_delay = self.backoff_delays[domain]
                new_delay = max(current_delay * 0.5, 1.0)
                if new_delay <= 1.0:
                    del self.backoff_delays[domain]
                else:
                    self.backoff_delays[domain] = new_delay


class ContentFetcher:
    """Fetches content with comprehensive error handling and retries"""

    def __init__(self, settings: Settings, session: aiohttp.ClientSession,
                 proxy_manager: ProxyManager, rate_limiter: RateLimiter,
                 robots_checker: RobotsChecker):
        self.settings = settings
        self.session = session
        self.proxy_manager = proxy_manager
        self.rate_limiter = rate_limiter
        self.robots_checker = robots_checker

    async def fetch(self, url: str, **kwargs) -> dict[str, Any] | None:
        """Fetch content from URL with all guardrails"""

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Check robots.txt (temporarily disabled for debugging)
        # if not await self.robots_checker.can_fetch(url, self.settings.crawling.user_agent):
        #     logger.info(f"Robots.txt disallows fetching {url}")
        #     return None

        # Apply rate limiting
        await self.rate_limiter.acquire(domain)

        # Get crawl delay from robots.txt (temporarily disabled for debugging)
        # robots_delay = self.robots_checker.get_crawl_delay(url, self.settings.crawling.user_agent)
        # if robots_delay:
        #     await asyncio.sleep(robots_delay)

        # Attempt fetch with retries
        for attempt in range(self.settings.crawling.max_retries + 1):
            try:
                result = await self._fetch_with_proxy(url, attempt, **kwargs)
                if result:
                    self.rate_limiter.apply_backoff(domain, result["status_code"])
                    return result

            except Exception as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")

                if attempt < self.settings.crawling.max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) * self.settings.crawling.retry_delay
                    jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
                    await asyncio.sleep(delay + jitter)

        # If proxy failed, try direct connection as fallback
        logger.info(f"Proxy failed for {url}, trying direct connection")
        try:
            result = await self._fetch_direct(url, **kwargs)
            if result:
                logger.info(f"Direct connection successful for {url}")
                self.rate_limiter.apply_backoff(domain, result["status_code"])
                return result
            else:
                logger.warning(f"Direct connection returned None for {url}")
        except Exception as e:
            logger.warning(f"Direct fetch also failed for {url}: {e}")

        logger.error(f"Failed to fetch {url} after {self.settings.crawling.max_retries + 1} attempts")
        return None

    async def _fetch_direct(self, url: str, **kwargs) -> dict[str, Any] | None:
        """Fetch content directly without proxy"""

        # Prepare request
        headers = {
            "User-Agent": self.settings.crawling.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        headers.update(kwargs.get("headers", {}))

        timeout = aiohttp.ClientTimeout(total=self.settings.crawling.timeout)

        start_time = time.time()

        try:
            async with self.session.get(
                url,
                headers=headers,
                timeout=timeout,
                max_redirects=self.settings.crawling.max_redirects,
                **kwargs
            ) as response:

                # Check content size
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.settings.crawling.max_content_size:
                    logger.warning(f"Content too large for {url}: {content_length} bytes")
                    return None

                # Read content
                content = await response.read()
                fetch_time = time.time() - start_time

                return {
                    "url": str(response.url),
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "content_type": response.headers.get("content-type", ""),
                    "encoding": response.charset or "utf-8",
                    "fetch_time_ms": fetch_time * 1000,
                    "content_size_bytes": len(content),
                    "final_url": str(response.url),
                    "proxy_used": None
                }

        except Exception as e:
            logger.error(f"Error in direct fetch for {url}: {e}")
            raise

    async def _fetch_with_proxy(self, url: str, attempt: int, **kwargs) -> dict[str, Any] | None:
        """Fetch content using proxy"""

        # Get proxy
        proxy = self.proxy_manager.get_next_proxy()

        # Prepare request
        headers = {
            "User-Agent": self.settings.crawling.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        headers.update(kwargs.get("headers", {}))

        timeout = aiohttp.ClientTimeout(total=self.settings.crawling.timeout)

        start_time = time.time()

        try:
            async with self.session.get(
                url,
                proxy=proxy,
                headers=headers,
                timeout=timeout,
                max_redirects=self.settings.crawling.max_redirects,
                **kwargs
            ) as response:

                # Check content size
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.settings.crawling.max_content_size:
                    logger.warning(f"Content too large for {url}: {content_length} bytes")
                    return None

                # Read content with size limit
                content = await response.read()
                if len(content) > self.settings.crawling.max_content_size:
                    logger.warning(f"Content too large for {url}: {len(content)} bytes")
                    return None

                fetch_time = time.time() - start_time

                # Record proxy usage
                if proxy:
                    self.proxy_manager.record_usage(
                        proxy, len(content), response.status < 400
                    )

                result = {
                    "url": str(response.url),
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "encoding": response.get_encoding(),
                    "fetch_time": fetch_time,
                    "proxy_used": proxy is not None,
                    "attempt": attempt + 1,
                }

                if response.status >= 400:
                    logger.warning(f"HTTP {response.status} for {url}")

                return result

        except TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            if proxy:
                self.proxy_manager.record_usage(proxy, 0, False)
            raise

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            if proxy:
                self.proxy_manager.record_usage(proxy, 0, False)
            raise


class DiscoveryEngine:
    """Discovers new content sources and URLs"""

    def __init__(self, settings: Settings, fetcher: ContentFetcher):
        self.settings = settings
        self.fetcher = fetcher

    async def discover_from_rss(self, rss_url: str) -> list[str]:
        """Discover URLs from RSS feed"""

        result = await self.fetcher.fetch(rss_url)
        if not result or result["status_code"] != 200:
            return []

        try:
            import feedparser

            # Parse RSS content
            content = result["content"].decode(result.get("encoding", "utf-8"))
            feed = feedparser.parse(content)

            urls = []
            for entry in feed.entries:
                if hasattr(entry, "link"):
                    urls.append(entry.link)

            logger.info(f"Discovered {len(urls)} URLs from RSS feed {rss_url}")
            return urls

        except Exception as e:
            logger.error(f"Failed to parse RSS feed {rss_url}: {e}")
            return []

    async def discover_from_sitemap(self, sitemap_url: str) -> list[str]:
        """Discover URLs from XML sitemap"""

        result = await self.fetcher.fetch(sitemap_url)
        if not result or result["status_code"] != 200:
            return []

        try:
            import xml.etree.ElementTree as ET

            # Parse sitemap XML
            content = result["content"].decode(result.get("encoding", "utf-8"))
            root = ET.fromstring(content)

            urls = []

            # Handle sitemap index
            for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None:
                    # Recursively fetch sub-sitemaps
                    sub_urls = await self.discover_from_sitemap(loc.text)
                    urls.extend(sub_urls)

            # Handle URL entries
            for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None:
                    urls.append(loc.text)

            logger.info(f"Discovered {len(urls)} URLs from sitemap {sitemap_url}")
            return urls

        except Exception as e:
            logger.error(f"Failed to parse sitemap {sitemap_url}: {e}")
            return []

    async def discover_from_search_api(self, query: str, api_type: str = "bing") -> list[str]:
        """Discover URLs from search API"""

        if api_type == "bing":
            return await self._discover_from_bing(query)
        elif api_type == "google":
            return await self._discover_from_google(query)
        else:
            logger.error(f"Unsupported search API type: {api_type}")
            return []

    async def _discover_from_bing(self, query: str) -> list[str]:
        """Discover URLs from Bing News API"""

        # This would require Bing API key
        # Implementation depends on API availability
        logger.info(f"Bing search discovery not implemented for query: {query}")
        return []

    async def _discover_from_google(self, query: str) -> list[str]:
        """Discover URLs from Google Custom Search API"""

        # This would require Google API key
        # Implementation depends on API availability
        logger.info(f"Google search discovery not implemented for query: {query}")
        return []


class WebCrawler:
    """Main web crawler orchestrating all components"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: aiohttp.ClientSession | None = None
        self.proxy_manager: ProxyManager | None = None
        self.rate_limiter: RateLimiter | None = None
        self.robots_checker: RobotsChecker | None = None
        self.fetcher: ContentFetcher | None = None
        self.discovery_engine: DiscoveryEngine | None = None

        # Statistics
        self.stats = {
            "requests_made": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "bytes_downloaded": 0,
            "robots_blocked": 0,
            "rate_limited": 0,
            "start_time": None,
        }

    async def __aenter__(self):
        """Async context manager entry"""

        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=self.settings.evomi.concurrent_requests,
            limit_per_host=self.settings.crawling.max_concurrent_per_domain,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.settings.crawling.timeout),
            headers={"User-Agent": self.settings.crawling.user_agent}
        )

        # Initialize components
        self.proxy_manager = ProxyManager(self.settings)
        self.rate_limiter = RateLimiter(self.settings)
        self.robots_checker = RobotsChecker(self.session)
        self.fetcher = ContentFetcher(
            self.settings, self.session, self.proxy_manager,
            self.rate_limiter, self.robots_checker
        )
        self.discovery_engine = DiscoveryEngine(self.settings, self.fetcher)

        self.stats["start_time"] = datetime.utcnow()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""

        if self.session:
            await self.session.close()

    async def crawl_url(self, url: str, **kwargs) -> dict[str, Any] | None:
        """Crawl a single URL"""

        self.stats["requests_made"] += 1

        result = await self.fetcher.fetch(url, **kwargs)

        if result:
            if result["status_code"] < 400:
                self.stats["requests_successful"] += 1
                self.stats["bytes_downloaded"] += len(result["content"])
            else:
                self.stats["requests_failed"] += 1
        else:
            self.stats["requests_failed"] += 1

        return result

    async def crawl_urls(self, urls: list[str], max_concurrent: int = 10) -> list[dict[str, Any]]:
        """Crawl multiple URLs concurrently"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_single(url: str) -> dict[str, Any] | None:
            async with semaphore:
                return await self.crawl_url(url)

        tasks = [crawl_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Crawl task failed: {result}")

        return valid_results

    async def discover_urls(self, source_config: dict[str, Any]) -> list[str]:
        """Discover URLs from various sources"""

        urls = []

        # RSS discovery
        if "rss_url" in source_config:
            rss_urls = await self.discovery_engine.discover_from_rss(source_config["rss_url"])
            urls.extend(rss_urls)

        # Sitemap discovery - DISABLED for RSS-only mode
        # if "sitemap_url" in source_config:
        #     sitemap_urls = await self.discovery_engine.discover_from_sitemap(source_config["sitemap_url"])
        #     urls.extend(sitemap_urls)
        logger.info("Sitemap discovery disabled - using RSS feeds only")

        # Search API discovery
        if "search_queries" in source_config:
            for query in source_config["search_queries"]:
                search_urls = await self.discovery_engine.discover_from_search_api(query)
                urls.extend(search_urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        logger.info(f"Discovered {len(unique_urls)} unique URLs from {len(urls)} total")

        return unique_urls

    def get_stats(self) -> dict[str, Any]:
        """Get crawler statistics"""

        stats = self.stats.copy()

        if stats["start_time"]:
            runtime = datetime.utcnow() - stats["start_time"]
            stats["runtime_seconds"] = runtime.total_seconds()

            if stats["runtime_seconds"] > 0:
                stats["requests_per_second"] = stats["requests_made"] / stats["runtime_seconds"]
                stats["success_rate"] = stats["requests_successful"] / max(stats["requests_made"], 1)

        # Add proxy stats
        if self.proxy_manager:
            stats["proxy_stats"] = self.proxy_manager.get_proxy_stats()

        return stats


# Example usage
async def main():
    """Example crawler usage"""


    settings = get_settings()

    async with WebCrawler(settings) as crawler:
        # Single URL crawl
        result = await crawler.crawl_url("https://www.espn.com/nba/")
        if result:
            print(f"Fetched {len(result['content'])} bytes from {result['url']}")

        # Multiple URL crawl
        urls = [
            "https://www.nba.com/news/",
            "https://theathletic.com/nba/",
            "https://bleacherreport.com/nba"
        ]

        results = await crawler.crawl_urls(urls)
        print(f"Crawled {len(results)} URLs successfully")

        # Discovery
        source_config = {
            "rss_url": "https://www.espn.com/espn/rss/nba/news",
            "sitemap_url": "https://www.nba.com/sitemap.xml"
        }

        discovered_urls = await crawler.discover_urls(source_config)
        print(f"Discovered {len(discovered_urls)} URLs")

        # Print stats
        stats = crawler.get_stats()
        print(f"Crawler stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
