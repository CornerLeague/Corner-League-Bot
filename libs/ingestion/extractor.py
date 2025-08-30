# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Content extraction, canonicalization, and deduplication.
Handles HTML parsing, content extraction, URL canonicalization, and near-duplicate detection.
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from datasketch import MinHash, MinHashLSH
from langdetect import detect
from readability import Document
from trafilatura import extract

logger = logging.getLogger(__name__)

__all__ = [
    "URLCanonicalizer",
    "CanonicalURLExtractor",
    "ContentHasher",
    "NearDuplicateDetector",
    "DuplicateDetector",
    "ContentExtractor",
    "ExtractionPipeline",
]


__all__ = [
    "URLCanonicalizer",
    "CanonicalURLExtractor",
    "ContentHasher",
    "NearDuplicateDetector",
    "DuplicateDetector",
    "ContentExtractor",
    "ExtractionPipeline",
]


class URLCanonicalizer:
    """Canonicalizes URLs for deduplication"""

    def __init__(self):
        # Parameters to remove from URLs
        self.utm_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic"
        }

        self.tracking_params = {
            "fbclid", "gclid", "dclid", "msclkid", "twclid", "_ga", "_gl",
            "mc_cid", "mc_eid", "ref", "referrer", "source", "campaign",
            "medium", "content", "term", "affiliate", "partner"
        }

        self.session_params = {
            "sessionid", "session_id", "sid", "jsessionid", "phpsessid",
            "aspsessionid", "cfid", "cftoken", "_t", "timestamp", "cache_bust"
        }

        # All parameters to remove
        self.params_to_remove = self.utm_params | self.tracking_params | self.session_params

    def canonicalize(self, url: str, follow_redirects: bool = True) -> str:
        """Canonicalize URL by normalizing and removing tracking parameters"""

        try:
            parsed = urlparse(url.strip())

            # Normalize scheme and netloc
            scheme = parsed.scheme.lower() if parsed.scheme else "https"
            netloc = parsed.netloc.lower()

            # Remove www. prefix (configurable)
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Normalize path
            path = parsed.path
            if not path:
                path = "/"

            # Remove trailing slash for non-root paths
            if len(path) > 1 and path.endswith("/"):
                path = path[:-1]

            # Clean and sort query parameters
            query_params = parse_qs(parsed.query, keep_blank_values=False)

            # Remove tracking parameters
            cleaned_params = {}
            for key, values in query_params.items():
                if key.lower() not in self.params_to_remove:
                    # Keep only the first value for each parameter
                    cleaned_params[key] = values[0] if values else ""

            # Sort parameters for consistency
            if cleaned_params:
                sorted_params = sorted(cleaned_params.items())
                query = urlencode(sorted_params)
            else:
                query = ""

            # Remove fragment
            fragment = ""

            # Reconstruct URL
            canonical_url = urlunparse((scheme, netloc, path, "", query, fragment))

            return canonical_url

        except Exception as e:
            logger.warning(f"Failed to canonicalize URL {url}: {e}")
            return url

    def extract_canonical_from_html(self, html_content: str, base_url: str) -> str | None:
        """Extract canonical URL from HTML <link rel="canonical"> tag"""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Look for canonical link
            canonical_link = soup.find("link", rel="canonical")
            if canonical_link and canonical_link.get("href"):
                canonical_url = canonical_link["href"]

                # Handle relative URLs
                if canonical_url.startswith("//"):
                    canonical_url = f"https:{canonical_url}"
                elif canonical_url.startswith("/"):
                    parsed_base = urlparse(base_url)
                    canonical_url = f"{parsed_base.scheme}://{parsed_base.netloc}{canonical_url}"
                elif not canonical_url.startswith(("http://", "https://")):
                    # Relative URL
                    from urllib.parse import urljoin
                    canonical_url = urljoin(base_url, canonical_url)

                return self.canonicalize(canonical_url)

        except Exception as e:
            logger.warning(f"Failed to extract canonical URL from HTML: {e}")

        return None




class ContentHasher:
    """Generates content hashes for deduplication"""

    def __init__(self):
        self.stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
            "her", "us", "them", "my", "your", "his", "its", "our", "their"
        }

    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent hashing"""

        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove punctuation and special characters
        text = re.sub(r"[^\w\s]", " ", text)

        # Remove stopwords
        words = text.split()
        words = [word for word in words if word not in self.stopwords and len(word) > 2]

        return " ".join(words)

    def generate_content_hash(self, title: str, text: str) -> str:
        """Generate SHA-256 hash of normalized content"""

        normalized_title = self.normalize_text(title)
        normalized_text = self.normalize_text(text)

        # Combine title and text
        combined_content = f"{normalized_title} {normalized_text}"

        # Generate hash
        content_hash = hashlib.sha256(combined_content.encode("utf-8")).hexdigest()

        return content_hash

    def generate_shingles(self, text: str, k: int = 3) -> set[str]:
        """Generate k-shingles from text for similarity detection"""

        normalized_text = self.normalize_text(text)
        words = normalized_text.split()

        if len(words) < k:
            return {normalized_text}

        shingles = set()
        for i in range(len(words) - k + 1):
            shingle = " ".join(words[i:i + k])
            shingles.add(shingle)

        return shingles

    def generate_minhash(self, text: str, num_perm: int = 128) -> MinHash:
        """Generate MinHash signature for similarity detection"""

        shingles = self.generate_shingles(text)

        minhash = MinHash(num_perm=num_perm)
        for shingle in shingles:
            minhash.update(shingle.encode("utf-8"))

        return minhash


class NearDuplicateDetector:
    """Detects near-duplicate content using MinHash LSH"""

    def __init__(self, threshold: float = 0.8, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.content_hashes: dict[str, str] = {}  # minhash -> content_hash
        self.hasher = ContentHasher()

    def add_content(self, content_hash: str, title: str, text: str) -> bool:
        """Add content to duplicate detection index"""

        try:
            # Generate MinHash
            combined_text = f"{title} {text}"
            minhash = self.hasher.generate_minhash(combined_text, self.num_perm)

            # Check for duplicates
            duplicates = self.lsh.query(minhash)

            if duplicates:
                logger.info(f"Found {len(duplicates)} near-duplicates for content {content_hash}")
                return False  # Is duplicate

            # Add to index
            self.lsh.insert(content_hash, minhash)
            self.content_hashes[content_hash] = content_hash

            return True  # Not duplicate

        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            return True  # Assume not duplicate on error

    def find_duplicates(self, title: str, text: str) -> list[str]:
        """Find near-duplicates of given content"""

        try:
            combined_text = f"{title} {text}"
            minhash = self.hasher.generate_minhash(combined_text, self.num_perm)

            duplicates = self.lsh.query(minhash)
            return list(duplicates)

        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []

    def get_similarity(self, hash1: str, hash2: str) -> float:
        """Get similarity score between two content hashes"""

        # This would require storing the MinHash objects
        # For now, return 0.0 as placeholder
        return 0.0

    def cleanup_old_entries(self, max_entries: int = 100000) -> None:
        """Remove old entries to prevent memory bloat"""

        if len(self.content_hashes) > max_entries:
            # Remove oldest entries (this is a simplified approach)
            # In production, you'd want to use a proper LRU cache
            entries_to_remove = len(self.content_hashes) - max_entries

            for i, content_hash in enumerate(list(self.content_hashes.keys())):
                if i >= entries_to_remove:
                    break

                try:
                    self.lsh.remove(content_hash)
                    del self.content_hashes[content_hash]
                except:
                    pass  # Ignore errors during cleanup




    The original implementation accepted a Redis client as the first
    positional argument. To maintain drop-in compatibility while using
    the newer ``NearDuplicateDetector`` implementation, this class
    ignores the optional Redis client argument and forwards any
    remaining parameters to ``NearDuplicateDetector``.
    """

    def __init__(self, _redis_client=None, *args, **kwargs):  # noqa: D401 - see class docstring
        super().__init__(*args, **kwargs)


class ContentExtractor:
    """Extracts and processes content from HTML."""

    def __init__(
        self,
        _settings: Any | None = None,
        canonical_extractor: URLCanonicalizer | None = None,
        duplicate_detector: NearDuplicateDetector | None = None,
    ):
        """Create a new :class:`ContentExtractor`.

        Previous versions required a ``settings`` object, a canonical URL
        extractor and an optional duplicate detector. These parameters are
        accepted for backward compatibility but are not required by the
        current implementation.
        """

        self.settings = _settings
        self.canonicalizer = canonical_extractor or URLCanonicalizer()
        self.hasher = ContentHasher()
        self.duplicate_detector = duplicate_detector

        # Sports-specific keywords for relevance detection
        self.sports_keywords = {
            "basketball": ["basketball", "nba", "wnba", "ncaa basketball", "march madness", "playoffs"],
            "football": ["football", "nfl", "ncaa football", "college football", "super bowl"],
            "baseball": ["baseball", "mlb", "world series", "playoffs", "spring training"],
            "soccer": ["soccer", "football", "mls", "fifa", "world cup", "premier league"],
            "hockey": ["hockey", "nhl", "stanley cup", "playoffs"],
            "tennis": ["tennis", "wimbledon", "us open", "french open", "australian open"],
            "golf": ["golf", "pga", "masters", "us open", "british open"],
            "olympics": ["olympics", "olympic games", "winter olympics", "summer olympics"],
        }

    def extract_content(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract structured content from HTML"""

        result = {
            "url": url,
            "canonical_url": None,
            "title": None,
            "text": None,
            "byline": None,
            "published_at": None,
            "language": None,
            "word_count": 0,
            "image_url": None,
            "content_hash": None,
            "sports_keywords": [],
            "entities": {},
            "content_type": None,
            "extraction_method": None,
            "extraction_success": False,
            "extraction_errors": [],
        }

        try:
            # Canonicalize URL
            result["canonical_url"] = self.canonicalizer.canonicalize(url)

            # Try to extract canonical URL from HTML
            html_canonical = self.canonicalizer.extract_canonical_from_html(html_content, url)
            if html_canonical:
                result["canonical_url"] = html_canonical

            # Try multiple extraction methods
            extraction_methods = [
                ("trafilatura", self._extract_with_trafilatura),
                ("readability", self._extract_with_readability),
                ("beautifulsoup", self._extract_with_beautifulsoup),
            ]

            for method_name, method_func in extraction_methods:
                try:
                    extracted = method_func(html_content, url)
                    if extracted and extracted.get("text") and len(extracted["text"]) > 100:
                        result.update(extracted)
                        result["extraction_method"] = method_name
                        result["extraction_success"] = True
                        break
                except Exception as e:
                    result["extraction_errors"].append(f"{method_name}: {e!s}")

            # Post-process extracted content
            if result["extraction_success"]:
                result = self._post_process_content(result)

            return result

        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            result["extraction_errors"].append(f"General error: {e!s}")
            return result

    def _extract_with_trafilatura(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract content using Trafilatura"""

        # Extract main content
        text = extract(html_content, include_comments=False, include_tables=False)

        if not text:
            raise ValueError("No content extracted")

        # Extract metadata
        from trafilatura.metadata import extract_metadata
        metadata = extract_metadata(html_content)

        result = {
            "text": text,
            "title": metadata.title if metadata else None,
            "byline": metadata.author if metadata else None,
            "published_at": metadata.date if metadata else None,
        }

        return result

    def _extract_with_readability(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract content using Readability"""

        doc = Document(html_content)

        result = {
            "text": doc.summary(),
            "title": doc.title(),
        }

        # Extract additional metadata with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Try to find byline
        byline_selectors = [
            'meta[name="author"]',
            ".byline", ".author", ".writer",
            '[rel="author"]', ".post-author"
        ]

        for selector in byline_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    result["byline"] = element.get("content")
                else:
                    result["byline"] = element.get_text(strip=True)
                break

        # Try to find publication date
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publishdate"]',
            'meta[name="date"]',
            "time[datetime]",
            ".publish-date", ".date", ".timestamp"
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    result["published_at"] = element.get("content")
                elif element.name == "time":
                    result["published_at"] = element.get("datetime") or element.get_text(strip=True)
                else:
                    result["published_at"] = element.get_text(strip=True)
                break

        return result

    def _extract_with_beautifulsoup(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract content using BeautifulSoup as fallback"""

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()

        # Try to find main content
        content_selectors = [
            "article", "main", ".content", ".post-content",
            ".article-body", ".story-body", "#content"
        ]

        text = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=" ", strip=True)
                if len(text) > 100:
                    break

        # Fallback to body
        if not text or len(text) < 100:
            body = soup.find("body")
            if body:
                text = body.get_text(separator=" ", strip=True)

        if not text:
            raise ValueError("No content found")

        # Extract title
        title = None
        title_element = soup.find("title")
        if title_element:
            title = title_element.get_text(strip=True)

        # Try h1 as backup
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        result = {
            "text": text,
            "title": title,
        }

        return result

    def _post_process_content(self, result: dict[str, Any]) -> dict[str, Any]:
        """Post-process extracted content"""

        # Clean and validate text
        if result.get("text"):
            text = result["text"]

            # Remove excessive whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Calculate word count
            result["word_count"] = len(text.split())

            # Update text
            result["text"] = text

        # Clean title
        if result.get("title"):
            title = result["title"]
            title = re.sub(r"\s+", " ", title).strip()

            # Remove site name from title (common pattern)
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) > 1:
                    title = parts[0].strip()

            result["title"] = title

        # Detect language
        if result.get("text"):
            try:
                result["language"] = detect(result["text"])
            except:
                result["language"] = "en"  # Default to English

        # Parse publication date
        if result.get("published_at"):
            result["published_at"] = self._parse_date(result["published_at"])

        # Generate content hash
        if result.get("title") and result.get("text"):
            result["content_hash"] = self.hasher.generate_content_hash(
                result["title"], result["text"]
            )

        # Extract sports keywords
        result["sports_keywords"] = self._extract_sports_keywords(result.get("text", ""))

        # Determine content type
        result["content_type"] = self._classify_content_type(
            result.get("title", ""), result.get("text", "")
        )

        return result

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse publication date from various formats"""

        if not date_str:
            return None

        # Common date formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
            "%Y-%m-%dT%H:%M:%S",    # ISO format without timezone
            "%Y-%m-%d %H:%M:%S",    # Standard format
            "%Y-%m-%d",             # Date only
            "%m/%d/%Y",             # US format
            "%d/%m/%Y",             # European format
            "%B %d, %Y",            # Long format
            "%b %d, %Y",            # Short format
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        # Try with dateutil as fallback
        try:
            from dateutil.parser import parse
            return parse(date_str)
        except:
            pass

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _extract_sports_keywords(self, text: str) -> list[str]:
        """Extract sports-related keywords from text"""

        if not text:
            return []

        text_lower = text.lower()
        found_keywords = []

        for sport, keywords in self.sports_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)

        return list(set(found_keywords))  # Remove duplicates

    def _classify_content_type(self, title: str, text: str) -> str | None:
        """Classify content type based on title and text"""

        combined_text = f"{title} {text}".lower()

        # Content type patterns
        patterns = {
            "game_recap": ["final score", "game recap", "box score", "highlights", "final:"],
            "breaking_news": ["breaking:", "just in:", "report:", "sources:", "exclusive:"],
            "analysis": ["analysis", "breakdown", "preview", "prediction", "outlook"],
            "trade": ["trade", "traded", "acquired", "signs", "contract", "deal"],
            "injury": ["injury", "injured", "hurt", "out for", "sidelined", "questionable"],
            "roster": ["roster", "lineup", "starting", "bench", "depth chart"],
            "interview": ["interview", "says", "speaks", "comments", "quotes"],
        }

        for content_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return content_type

        return "general"


# Main extraction pipeline
class ExtractionPipeline:
    """Complete extraction pipeline with deduplication"""

    def __init__(self, duplicate_threshold: float = 0.8):
        self.extractor = ContentExtractor()
        self.duplicate_detector = NearDuplicateDetector(threshold=duplicate_threshold)

    def process_content(self, html_content: str, url: str) -> dict[str, Any]:
        """Process HTML content through complete extraction pipeline"""

        # Extract content
        result = self.extractor.extract_content(html_content, url)

        # Check for duplicates if extraction was successful
        if result["extraction_success"] and result.get("content_hash"):
            is_unique = self.duplicate_detector.add_content(
                result["content_hash"],
                result.get("title", ""),
                result.get("text", "")
            )

            result["is_duplicate"] = not is_unique

            if not is_unique:
                duplicates = self.duplicate_detector.find_duplicates(
                    result.get("title", ""),
                    result.get("text", "")
                )
                result["duplicate_of"] = duplicates
        else:
            result["is_duplicate"] = False

        return result

    def cleanup_duplicates(self) -> None:
        """Clean up old duplicate detection entries"""
        self.duplicate_detector.cleanup_old_entries()


# Example usage
async def main():
    """Example extraction usage"""

    pipeline = ExtractionPipeline()

    # Example HTML content
    html_content = """
    <html>
    <head>
        <title>Lakers Beat Warriors 120-115 in Overtime Thriller</title>
        <meta name="author" content="John Smith">
        <meta property="article:published_time" content="2024-01-15T22:30:00Z">
        <link rel="canonical" href="https://example.com/lakers-warriors-recap">
    </head>
    <body>
        <article>
            <h1>Lakers Beat Warriors 120-115 in Overtime Thriller</h1>
            <p>The Los Angeles Lakers defeated the Golden State Warriors 120-115 in an
            overtime thriller at Crypto.com Arena on Monday night. LeBron James led
            the Lakers with 35 points and 12 assists, while Stephen Curry scored
            42 points for the Warriors in the losing effort.</p>
            <p>The game was tied 110-110 at the end of regulation before the Lakers
            outscored the Warriors 10-5 in the extra period to secure the victory.</p>
        </article>
    </body>
    </html>
    """

    url = "https://example.com/lakers-warriors-game"

    # Process content
    result = pipeline.process_content(html_content, url)

    print(f"Extraction successful: {result['extraction_success']}")
    print(f"Title: {result['title']}")
    print(f"Canonical URL: {result['canonical_url']}")
    print(f"Word count: {result['word_count']}")
    print(f"Sports keywords: {result['sports_keywords']}")
    print(f"Content type: {result['content_type']}")
    print(f"Is duplicate: {result['is_duplicate']}")
    print(f"Content hash: {result['content_hash']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
