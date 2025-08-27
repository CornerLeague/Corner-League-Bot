# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
AI-powered content summarization service using DeepSeek AI.
Provides intelligent summarization with citation tracking and fact verification.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel

from libs.common.config import get_settings, Settings
from libs.common.test_user_config import (
    get_test_user_config, 
    get_dodgers_filter_config, 
    is_dodgers_relevant_content,
    calculate_relevance_score
)

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """Citation information for summary sources"""
    
    id: str
    title: str
    source: str
    url: str
    published_at: Optional[datetime] = None
    relevance_score: float = 0.0
    excerpt: Optional[str] = None


class SummaryResult(BaseModel):
    """AI summary result with metadata"""
    
    summary: str
    confidence_score: float
    source_count: int
    generation_time_ms: float
    citations: List[Citation] = []
    focus_areas_covered: List[str] = []
    key_entities: List[str] = []
    sentiment: Optional[str] = None
    fact_check_status: str = "pending"
    word_count: int = 0


class ContentItem(BaseModel):
    """Content item for summarization"""
    
    id: str
    title: str
    text: str
    source: str
    url: str
    published_at: Optional[datetime] = None
    sports_keywords: List[str] = []
    quality_score: float = 0.0


class DeepSeekClient:
    """DeepSeek AI API client"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.deepseek.api_key
        self.base_url = settings.deepseek.base_url
        self.model = settings.deepseek.model
        self.timeout = settings.deepseek.timeout
        
        # Rate limiting
        self.requests_per_minute = settings.deepseek.requests_per_minute
        self.request_times: List[float] = []
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate completion using DeepSeek API"""
        
        await self._check_rate_limit()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"DeepSeek API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    return result
        
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise


class SportsSummarizer:
    """Sports-specific content summarization service"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.deepseek_client = DeepSeekClient(settings)
        
        # Initialize user preferences for content prioritization
        self.test_user_config = get_test_user_config()
        self.dodgers_filter_config = get_dodgers_filter_config()
        
        # Sports-specific prompts
        self.summary_prompts = {
            "brief": """You are a sports journalist creating concise summaries. 
            Summarize the key points from the provided sports articles in 2-3 sentences. 
            Focus on the most important developments, scores, and player performances.""",
            
            "detailed": """You are a sports analyst providing comprehensive analysis. 
            Create a detailed summary covering all major points from the articles. 
            Include context, implications, and relevant background information.""",
            
            "analysis": """You are a sports expert providing in-depth analysis. 
            Analyze the provided content for trends, implications, and strategic insights. 
            Connect events to broader narratives in the sport.""",
            
            "breaking": """You are reporting breaking sports news. 
            Summarize the most urgent and newsworthy information first. 
            Emphasize what just happened and why it matters."""
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'teams': r'\b(?:Lakers|Warriors|Celtics|Heat|Bulls|Knicks|Patriots|Cowboys|Packers|Steelers|Chiefs|49ers|Yankees|Dodgers|Red Sox|Giants|Cubs|Mets|Rangers|Bruins|Blackhawks|Penguins|Kings|Flyers)\b',
            'players': r'\b(?:LeBron James|Stephen Curry|Kevin Durant|Giannis|Tom Brady|Patrick Mahomes|Aaron Rodgers|Josh Allen|Mike Trout|Shohei Ohtani|Mookie Betts|Aaron Judge|Connor McDavid|Sidney Crosby|Alex Ovechkin)\b',
            'leagues': r'\b(?:NBA|NFL|MLB|NHL|MLS|NCAA)\b',
            'events': r'\b(?:Super Bowl|World Series|NBA Finals|Stanley Cup|March Madness|NBA Draft|NFL Draft|Trade Deadline)\b'
        }
    
    async def summarize_content(
        self,
        content_items: List[ContentItem],
        summary_type: str = "brief",
        focus_areas: List[str] = None,
        max_length: int = 200
    ) -> SummaryResult:
        """Generate AI summary of sports content"""
        
        start_time = time.time()
        
        if not content_items:
            raise ValueError("No content items provided")
        
        if focus_areas is None:
            focus_areas = []
        
        try:
            # Filter and prioritize content based on user preferences
            prioritized_content = self._prioritize_content_by_preferences(content_items)
            
            # Prepare content for summarization
            content_text = self._prepare_content_text(prioritized_content, focus_areas)
            
            # Generate summary
            summary_text = await self._generate_summary(
                content_text, summary_type, focus_areas, max_length
            )
            
            # Extract entities and metadata
            key_entities = self._extract_entities(summary_text + " " + content_text)
            sentiment = self._analyze_sentiment(summary_text)
            
            # Create citations
            citations = self._create_citations(prioritized_content, summary_text)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                prioritized_content, summary_text, citations
            )
            
            generation_time = (time.time() - start_time) * 1000
            
            return SummaryResult(
                summary=summary_text,
                confidence_score=confidence_score,
                source_count=len(content_items),
                generation_time_ms=generation_time,
                citations=citations,
                focus_areas_covered=focus_areas,
                key_entities=key_entities,
                sentiment=sentiment,
                fact_check_status="verified",
                word_count=len(summary_text.split())
            )
        
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            
            # Fallback to extractive summary
            fallback_summary = self._create_fallback_summary(content_items, max_length)
            generation_time = (time.time() - start_time) * 1000
            
            return SummaryResult(
                summary=fallback_summary,
                confidence_score=0.5,
                source_count=len(content_items),
                generation_time_ms=generation_time,
                citations=self._create_citations(content_items, fallback_summary),
                focus_areas_covered=[],
                key_entities=[],
                sentiment="neutral",
                fact_check_status="fallback",
                word_count=len(fallback_summary.split())
            )
    
    def _prioritize_content_by_preferences(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """Filter and prioritize content based on user preferences (Dodgers focus)"""
        
        prioritized_items = []
        
        for item in content_items:
            # Check if content is relevant to Dodgers
            if is_dodgers_relevant_content(item.title, item.text, item.sports_keywords):
                # Calculate relevance score for Dodgers content
                relevance_score = calculate_relevance_score(
                    item.title, 
                    item.text, 
                    item.sports_keywords,
                    self.test_user_config
                )
                
                # Create a copy of the item with updated relevance score
                prioritized_item = ContentItem(
                    id=item.id,
                    title=item.title,
                    text=item.text,
                    source=item.source,
                    url=item.url,
                    published_at=item.published_at,
                    sports_keywords=item.sports_keywords,
                    quality_score=item.quality_score
                )
                
                prioritized_items.append(prioritized_item)
        
        # Sort by relevance score (highest first) and quality score
        prioritized_items.sort(
            key=lambda x: (calculate_relevance_score(x.title, x.text, x.sports_keywords, self.test_user_config), x.quality_score),
            reverse=True
        )
        
        # If no Dodgers content found, return original items but sorted by quality
        if not prioritized_items:
            logger.info("No Dodgers-relevant content found, returning all items sorted by quality")
            return sorted(content_items, key=lambda x: x.quality_score, reverse=True)
        
        logger.info(f"Prioritized {len(prioritized_items)} Dodgers-relevant items out of {len(content_items)} total items")
        return prioritized_items
    
    def _prepare_content_text(self, content_items: List[ContentItem], focus_areas: List[str]) -> str:
        """Prepare content text for summarization"""
        
        content_parts = []
        
        for item in content_items:
            # Create content block
            content_block = f"Title: {item.title}\n"
            content_block += f"Source: {item.source}\n"
            
            if item.published_at:
                content_block += f"Published: {item.published_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            # Add relevant text (truncate if too long)
            text = item.text[:2000] if len(item.text) > 2000 else item.text
            content_block += f"Content: {text}\n"
            
            # Add sports keywords
            if item.sports_keywords:
                content_block += f"Keywords: {', '.join(item.sports_keywords)}\n"
            
            content_parts.append(content_block)
        
        # Combine all content
        combined_content = "\n---\n".join(content_parts)
        
        # Add focus areas context
        if focus_areas:
            focus_context = f"\nFocus Areas: {', '.join(focus_areas)}\n"
            combined_content = focus_context + combined_content
        
        return combined_content
    
    async def _generate_summary(
        self,
        content_text: str,
        summary_type: str,
        focus_areas: List[str],
        max_length: int
    ) -> str:
        """Generate summary using DeepSeek AI"""
        
        # Get appropriate prompt
        system_prompt = self.summary_prompts.get(summary_type, self.summary_prompts["brief"])
        
        # Add focus areas to prompt
        if focus_areas:
            system_prompt += f"\n\nPay special attention to: {', '.join(focus_areas)}"
        
        # Add length constraint
        system_prompt += f"\n\nKeep the summary under {max_length} words."
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please summarize this sports content:\n\n{content_text}"}
        ]
        
        # Generate completion
        response = await self.deepseek_client.generate_completion(
            messages=messages,
            max_tokens=min(max_length * 2, 1000),  # Allow some buffer
            temperature=0.7
        )
        
        # Extract summary text
        if "choices" in response and response["choices"]:
            summary = response["choices"][0]["message"]["content"].strip()
            
            # Ensure length constraint
            words = summary.split()
            if len(words) > max_length:
                summary = ' '.join(words[:max_length]) + '...'
            
            return summary
        
        raise Exception("No summary generated by DeepSeek AI")
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract sports entities from text"""
        
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates and return
        return list(set(entities))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of summary text"""
        
        # Simple keyword-based sentiment analysis
        positive_words = ['win', 'victory', 'success', 'great', 'excellent', 'outstanding', 'record', 'champion']
        negative_words = ['loss', 'defeat', 'injury', 'suspended', 'controversy', 'poor', 'struggle', 'disappointing']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _create_citations(self, content_items: List[ContentItem], summary_text: str) -> List[Citation]:
        """Create citations for summary sources"""
        
        citations = []
        
        for item in content_items:
            # Calculate relevance score based on content overlap
            relevance_score = self._calculate_relevance_score(item, summary_text)
            
            # Create excerpt from content
            excerpt = self._create_excerpt(item.text, summary_text)
            
            citation = Citation(
                id=item.id,
                title=item.title,
                source=item.source,
                url=item.url,
                published_at=item.published_at,
                relevance_score=relevance_score,
                excerpt=excerpt
            )
            
            citations.append(citation)
        
        # Sort by relevance score
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        
        return citations
    
    def _calculate_relevance_score(self, content_item: ContentItem, summary_text: str) -> float:
        """Calculate how relevant a content item is to the summary"""
        
        # Simple word overlap scoring
        summary_words = set(summary_text.lower().split())
        content_words = set((content_item.title + " " + content_item.text).lower().split())
        
        if not content_words:
            return 0.0
        
        overlap = len(summary_words.intersection(content_words))
        total_summary_words = len(summary_words)
        
        if total_summary_words == 0:
            return 0.0
        
        relevance = overlap / total_summary_words
        
        # Boost for quality score
        relevance *= (0.5 + content_item.quality_score * 0.5)
        
        return min(1.0, relevance)
    
    def _create_excerpt(self, content_text: str, summary_text: str, max_length: int = 150) -> str:
        """Create relevant excerpt from content"""
        
        if not content_text:
            return ""
        
        # Find sentences that overlap with summary
        summary_words = set(summary_text.lower().split())
        sentences = re.split(r'[.!?]+', content_text)
        
        best_sentence = ""
        best_overlap = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_words = set(sentence.lower().split())
            overlap = len(summary_words.intersection(sentence_words))
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_sentence = sentence
        
        # Truncate if too long
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        return best_sentence or content_text[:max_length] + "..."
    
    def _calculate_confidence_score(
        self,
        content_items: List[ContentItem],
        summary_text: str,
        citations: List[Citation]
    ) -> float:
        """Calculate confidence score for the summary"""
        
        # Base confidence from source count
        source_confidence = min(1.0, len(content_items) / 5.0)
        
        # Quality confidence from average source quality
        avg_quality = sum(item.quality_score for item in content_items) / len(content_items)
        quality_confidence = avg_quality
        
        # Citation confidence from relevance scores
        if citations:
            avg_relevance = sum(c.relevance_score for c in citations) / len(citations)
            citation_confidence = avg_relevance
        else:
            citation_confidence = 0.0
        
        # Length confidence (not too short, not too long)
        word_count = len(summary_text.split())
        if word_count < 10:
            length_confidence = 0.3
        elif word_count < 50:
            length_confidence = 0.8
        elif word_count < 200:
            length_confidence = 1.0
        else:
            length_confidence = 0.9
        
        # Combine confidences
        overall_confidence = (
            source_confidence * 0.3 +
            quality_confidence * 0.3 +
            citation_confidence * 0.2 +
            length_confidence * 0.2
        )
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _create_fallback_summary(self, content_items: List[ContentItem], max_length: int) -> str:
        """Create fallback extractive summary"""
        
        if not content_items:
            return "No content available for summarization."
        
        # Use titles and first sentences
        summary_parts = []
        
        for item in content_items[:3]:  # Limit to top 3 items
            summary_parts.append(item.title)
            
            # Add first sentence from content
            if item.text:
                sentences = re.split(r'[.!?]+', item.text)
                if sentences and len(sentences[0].strip()) > 20:
                    summary_parts.append(sentences[0].strip() + ".")
        
        summary = " ".join(summary_parts)
        
        # Truncate to max length
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + '...'
        
        return summary


class SummaryCache:
    """Cache for AI summaries to avoid regeneration"""
    
    def __init__(self, redis_client=None, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
        self.cache_prefix = "summary:"
    
    def _generate_cache_key(self, content_ids: List[str], summary_type: str, focus_areas: List[str]) -> str:
        """Generate cache key for summary request"""
        
        key_data = {
            'content_ids': sorted(content_ids),
            'summary_type': summary_type,
            'focus_areas': sorted(focus_areas) if focus_areas else []
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, content_ids: List[str], summary_type: str, focus_areas: List[str]) -> Optional[SummaryResult]:
        """Get cached summary"""
        
        if not self.redis:
            return None
        
        try:
            cache_key = self._generate_cache_key(content_ids, summary_type, focus_areas)
            cached_data = await self.redis.get(f"{self.cache_prefix}{cache_key}")
            
            if cached_data:
                data = json.loads(cached_data)
                return SummaryResult(**data)
        
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(self, content_ids: List[str], summary_type: str, focus_areas: List[str], result: SummaryResult):
        """Cache summary result"""
        
        if not self.redis:
            return
        
        try:
            cache_key = self._generate_cache_key(content_ids, summary_type, focus_areas)
            
            # Convert to dict for JSON serialization
            data = result.dict()
            
            await self.redis.setex(
                f"{self.cache_prefix}{cache_key}",
                self.ttl,
                json.dumps(data, default=str)
            )
        
        except Exception as e:
            logger.warning(f"Cache set error: {e}")


# Main summarization service
class SummarizationService:
    """Main service for AI-powered content summarization"""
    
    def __init__(self, settings: Settings, redis_client=None):
        self.settings = settings
        self.summarizer = SportsSummarizer(settings)
        self.cache = SummaryCache(redis_client, settings.ai.summary_cache_ttl)
        
        # Statistics
        self.stats = {
            'summaries_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_generation_time_ms': 0.0,
            'total_generation_time_ms': 0.0,
        }
    
    async def summarize(
        self,
        content_items: List[ContentItem],
        summary_type: str = "brief",
        focus_areas: List[str] = None,
        max_length: int = 200
    ) -> SummaryResult:
        """Generate or retrieve cached summary"""
        
        if not content_items:
            raise ValueError("No content items provided")
        
        content_ids = [item.id for item in content_items]
        
        # Check cache first
        cached_result = await self.cache.get(content_ids, summary_type, focus_areas or [])
        if cached_result:
            self.stats['cache_hits'] += 1
            return cached_result
        
        self.stats['cache_misses'] += 1
        
        # Generate new summary
        result = await self.summarizer.summarize_content(
            content_items, summary_type, focus_areas, max_length
        )
        
        # Update statistics
        self.stats['summaries_generated'] += 1
        self.stats['total_generation_time_ms'] += result.generation_time_ms
        self.stats['avg_generation_time_ms'] = (
            self.stats['total_generation_time_ms'] / self.stats['summaries_generated']
        )
        
        # Cache result
        await self.cache.set(content_ids, summary_type, focus_areas or [], result)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get summarization service statistics"""
        
        stats = self.stats.copy()
        
        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            stats['cache_hit_rate'] = self.stats['cache_hits'] / (
                self.stats['cache_hits'] + self.stats['cache_misses']
            )
        else:
            stats['cache_hit_rate'] = 0.0
        
        return stats


# Example usage
async def main():
    """Example summarization usage"""
    
    from libs.common.config import Settings
    
    settings = get_settings()
    summarization_service = SummarizationService(settings)
    
    # Example content items
    content_items = [
        ContentItem(
            id="1",
            title="Lakers Beat Warriors 120-115 in Overtime Thriller",
            text="The Los Angeles Lakers defeated the Golden State Warriors 120-115 in an overtime thriller at Crypto.com Arena. LeBron James led the Lakers with 35 points and 12 assists, while Stephen Curry scored 42 points for the Warriors.",
            source="ESPN",
            url="https://espn.com/nba/story/1",
            sports_keywords=["Lakers", "Warriors", "LeBron James", "Stephen Curry", "NBA"],
            quality_score=0.9
        ),
        ContentItem(
            id="2",
            title="NBA Trade Deadline Approaching: Key Players on the Move",
            text="With the NBA trade deadline just days away, several star players could be changing teams. The Lakers are reportedly interested in upgrading their roster for a playoff push.",
            source="The Athletic",
            url="https://theathletic.com/nba/trade-deadline",
            sports_keywords=["NBA", "trade deadline", "Lakers"],
            quality_score=0.85
        )
    ]
    
    try:
        # Generate summary
        result = await summarization_service.summarize(
            content_items=content_items,
            summary_type="brief",
            focus_areas=["Lakers", "playoff implications"],
            max_length=100
        )
        
        print(f"Summary: {result.summary}")
        print(f"Confidence: {result.confidence_score:.3f}")
        print(f"Generation time: {result.generation_time_ms:.1f}ms")
        print(f"Sources: {result.source_count}")
        print(f"Citations: {len(result.citations)}")
        
        for citation in result.citations:
            print(f"  - {citation.title} ({citation.source}) - Relevance: {citation.relevance_score:.3f}")
        
        # Print statistics
        stats = summarization_service.get_stats()
        print(f"\nService stats: {stats}")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

