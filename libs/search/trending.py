# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Trending detection system with discovery feedback loop.
Detects trending sports topics and feeds them back to content discovery.
"""

import asyncio
import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from libs.common.config import get_settings, Settings
from libs.common.database import ConnectionPool

logger = logging.getLogger(__name__)


class TrendingTerm:
    """Represents a trending term with metrics"""
    
    def __init__(self, term: str, normalized_term: str, term_type: str = "general"):
        self.term = term
        self.normalized_term = normalized_term
        self.term_type = term_type
        
        # Time-windowed counts
        self.count_1h = 0
        self.count_6h = 0
        self.count_24h = 0
        
        # Trending metrics
        self.burst_ratio = 0.0
        self.trend_score = 0.0
        self.is_trending = False
        
        # Metadata
        self.trend_start: Optional[datetime] = None
        self.trend_peak: Optional[datetime] = None
        self.last_seen = datetime.utcnow()
        self.related_terms: List[str] = []
        self.sports_context: Dict[str, Any] = {}
    
    def update_counts(self, count_1h: int, count_6h: int, count_24h: int):
        """Update time-windowed counts"""
        self.count_1h = count_1h
        self.count_6h = count_6h
        self.count_24h = count_24h
        self.last_seen = datetime.utcnow()
    
    def calculate_burst_ratio(self) -> float:
        """Calculate burst ratio: (2h rate) / (24h average rate)"""
        
        if self.count_24h == 0:
            return 0.0
        
        # Estimate 2h count from 1h and 6h
        count_2h = min(self.count_1h * 2, self.count_6h)
        
        # Calculate rates (per hour)
        rate_2h = count_2h / 2.0
        rate_24h = self.count_24h / 24.0
        
        if rate_24h == 0:
            return 0.0
        
        self.burst_ratio = rate_2h / rate_24h
        return self.burst_ratio
    
    def calculate_trend_score(self, settings: Settings) -> float:
        """Calculate overall trend score"""
        
        # Base score from burst ratio
        burst_score = min(1.0, self.burst_ratio / 10.0)  # Normalize to 0-1
        
        # Volume score (logarithmic)
        volume_score = min(1.0, math.log10(max(1, self.count_1h)) / 3.0)
        
        # Recency bonus
        time_since_seen = (datetime.utcnow() - self.last_seen).total_seconds() / 3600
        recency_score = max(0.0, 1.0 - time_since_seen / 6.0)  # Decay over 6 hours
        
        # Sports context bonus
        context_score = 0.0
        if self.sports_context:
            context_score = 0.2  # Bonus for sports-specific terms
        
        # Combine scores
        self.trend_score = (
            burst_score * 0.4 +
            volume_score * 0.3 +
            recency_score * 0.2 +
            context_score * 0.1
        )
        
        return self.trend_score
    
    def is_trending_now(self, settings: Settings) -> bool:
        """Check if term is currently trending"""
        
        self.calculate_burst_ratio()
        self.calculate_trend_score(settings)
        
        # Trending criteria
        meets_burst_threshold = self.burst_ratio >= settings.trending.min_burst_ratio
        meets_score_threshold = self.trend_score >= settings.trending.min_trend_score
        meets_volume_threshold = self.count_1h >= settings.trending.min_occurrences
        
        was_trending = self.is_trending
        self.is_trending = meets_burst_threshold and meets_score_threshold and meets_volume_threshold
        
        # Track trend lifecycle
        if self.is_trending and not was_trending:
            self.trend_start = datetime.utcnow()
        
        if self.is_trending:
            self.trend_peak = datetime.utcnow()
        
        return self.is_trending
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage"""
        
        return {
            'term': self.term,
            'normalized_term': self.normalized_term,
            'term_type': self.term_type,
            'count_1h': self.count_1h,
            'count_6h': self.count_6h,
            'count_24h': self.count_24h,
            'burst_ratio': self.burst_ratio,
            'trend_score': self.trend_score,
            'is_trending': self.is_trending,
            'trend_start': self.trend_start.isoformat() if self.trend_start else None,
            'trend_peak': self.trend_peak.isoformat() if self.trend_peak else None,
            'last_seen': self.last_seen.isoformat(),
            'related_terms': self.related_terms,
            'sports_context': self.sports_context,
        }


class TermExtractor:
    """Extracts and normalizes terms from content"""
    
    def __init__(self):
        # Sports-specific term patterns
        self.sports_entities = {
            'teams': [
                'Lakers', 'Warriors', 'Celtics', 'Heat', 'Bulls', 'Knicks',
                'Patriots', 'Cowboys', 'Packers', 'Steelers', 'Chiefs', '49ers',
                'Yankees', 'Dodgers', 'Red Sox', 'Giants', 'Cubs', 'Mets',
                'Rangers', 'Bruins', 'Blackhawks', 'Penguins', 'Kings', 'Flyers'
            ],
            'players': [
                'LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis',
                'Tom Brady', 'Patrick Mahomes', 'Aaron Rodgers', 'Josh Allen',
                'Mike Trout', 'Shohei Ohtani', 'Mookie Betts', 'Aaron Judge',
                'Connor McDavid', 'Sidney Crosby', 'Alex Ovechkin'
            ],
            'leagues': ['NBA', 'NFL', 'MLB', 'NHL', 'MLS', 'NCAA'],
            'events': [
                'Super Bowl', 'World Series', 'NBA Finals', 'Stanley Cup',
                'March Madness', 'NBA Draft', 'NFL Draft', 'Trade Deadline'
            ]
        }
        
        # Stopwords to exclude
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
    
    def extract_terms(self, title: str, text: str, sports_keywords: List[str]) -> List[Tuple[str, str, str]]:
        """Extract terms from content (term, normalized_term, term_type)"""
        
        terms = []
        combined_text = f"{title} {text}".lower()
        
        # Extract sports keywords
        for keyword in sports_keywords:
            normalized = self._normalize_term(keyword)
            if normalized:
                term_type = self._classify_term(keyword)
                terms.append((keyword, normalized, term_type))
        
        # Extract named entities
        for entity_type, entities in self.sports_entities.items():
            for entity in entities:
                if entity.lower() in combined_text:
                    normalized = self._normalize_term(entity)
                    if normalized:
                        terms.append((entity, normalized, entity_type))
        
        # Extract significant phrases (2-3 words)
        words = combined_text.split()
        for i in range(len(words) - 1):
            # 2-word phrases
            phrase = f"{words[i]} {words[i+1]}"
            if self._is_significant_phrase(phrase):
                normalized = self._normalize_term(phrase)
                if normalized:
                    terms.append((phrase, normalized, 'phrase'))
            
            # 3-word phrases
            if i < len(words) - 2:
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                if self._is_significant_phrase(phrase):
                    normalized = self._normalize_term(phrase)
                    if normalized:
                        terms.append((phrase, normalized, 'phrase'))
        
        return terms
    
    def _normalize_term(self, term: str) -> str:
        """Normalize term for consistent tracking"""
        
        # Convert to lowercase
        normalized = term.lower().strip()
        
        # Remove punctuation
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Skip if too short or is stopword
        if len(normalized) < 3 or normalized in self.stopwords:
            return ""
        
        return normalized
    
    def _classify_term(self, term: str) -> str:
        """Classify term type"""
        
        term_lower = term.lower()
        
        for entity_type, entities in self.sports_entities.items():
            for entity in entities:
                if entity.lower() == term_lower:
                    return entity_type
        
        # Default classification
        if len(term.split()) == 1:
            return 'keyword'
        else:
            return 'phrase'
    
    def _is_significant_phrase(self, phrase: str) -> bool:
        """Check if phrase is significant enough to track"""
        
        words = phrase.split()
        
        # Skip if contains stopwords
        if any(word in self.stopwords for word in words):
            return False
        
        # Skip if too short
        if len(phrase) < 6:
            return False
        
        # Check for sports relevance
        sports_indicators = [
            'game', 'match', 'season', 'player', 'team', 'coach', 'trade',
            'injury', 'score', 'win', 'loss', 'championship', 'playoff'
        ]
        
        if any(indicator in phrase for indicator in sports_indicators):
            return True
        
        return False


class TrendingDetector:
    """Main trending detection engine"""
    
    def __init__(self, settings: Settings, connection_pool: ConnectionPool):
        self.settings = settings
        self.pool = connection_pool
        self.extractor = TermExtractor()
        
        # In-memory trending terms cache
        self.trending_terms: Dict[str, TrendingTerm] = {}
        
        # Cooldown tracking
        self.cooldown_terms: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            'terms_processed': 0,
            'trending_detected': 0,
            'queries_generated': 0,
            'last_update': None,
        }
    
    async def process_content(self, content: Dict[str, Any]) -> List[str]:
        """Process content and extract trending terms"""
        
        title = content.get('title', '')
        text = content.get('text', '')
        sports_keywords = content.get('sports_keywords', [])
        
        # Extract terms
        extracted_terms = self.extractor.extract_terms(title, text, sports_keywords)
        
        processed_terms = []
        for term, normalized_term, term_type in extracted_terms:
            # Update term counts
            await self._update_term_counts(normalized_term, term, term_type)
            processed_terms.append(normalized_term)
        
        self.stats['terms_processed'] += len(processed_terms)
        
        return processed_terms
    
    async def detect_trending(self) -> List[TrendingTerm]:
        """Detect currently trending terms"""
        
        # Update all term metrics
        await self._update_all_term_metrics()
        
        # Find trending terms
        trending = []
        for term in self.trending_terms.values():
            if term.is_trending_now(self.settings):
                # Check cooldown
                if not self._is_in_cooldown(term.normalized_term):
                    trending.append(term)
        
        # Sort by trend score
        trending.sort(key=lambda t: t.trend_score, reverse=True)
        
        # Limit number of trending terms
        trending = trending[:self.settings.trending.max_trending_terms]
        
        self.stats['trending_detected'] = len(trending)
        self.stats['last_update'] = datetime.utcnow()
        
        return trending
    
    async def generate_discovery_queries(self, trending_terms: List[TrendingTerm]) -> List[Dict[str, Any]]:
        """Generate search queries for trending terms"""
        
        queries = []
        
        for term in trending_terms:
            # Skip if in cooldown
            if self._is_in_cooldown(term.normalized_term):
                continue
            
            # Generate base query
            base_query = term.term
            
            # Enhance query with context
            if term.sports_context:
                sport = term.sports_context.get('sport')
                if sport:
                    base_query = f"{base_query} {sport}"
            
            # Generate variations
            query_variations = [
                base_query,
                f"{base_query} news",
                f"{base_query} update",
                f"{base_query} latest",
            ]
            
            # Add related terms
            for related in term.related_terms[:2]:  # Limit to 2 related terms
                query_variations.append(f"{base_query} {related}")
            
            # Create query objects
            for query_text in query_variations:
                query_obj = {
                    'query': query_text,
                    'trending_term': term.normalized_term,
                    'trend_score': term.trend_score,
                    'burst_ratio': term.burst_ratio,
                    'priority': self._calculate_query_priority(term),
                    'generated_at': datetime.utcnow().isoformat(),
                    'cooldown_until': (datetime.utcnow() + timedelta(hours=self.settings.trending.cooldown_hours)).isoformat()
                }
                queries.append(query_obj)
            
            # Add to cooldown
            self._add_to_cooldown(term.normalized_term)
        
        # Sort by priority
        queries.sort(key=lambda q: q['priority'], reverse=True)
        
        self.stats['queries_generated'] += len(queries)
        
        return queries
    
    async def _update_term_counts(self, normalized_term: str, original_term: str, term_type: str):
        """Update term counts in database and cache"""
        
        # Get or create trending term
        if normalized_term not in self.trending_terms:
            self.trending_terms[normalized_term] = TrendingTerm(
                original_term, normalized_term, term_type
            )
        
        term_obj = self.trending_terms[normalized_term]
        
        # Update in database
        await self._upsert_term_in_db(term_obj)
        
        # Update counts from database
        counts = await self._get_term_counts_from_db(normalized_term)
        if counts:
            term_obj.update_counts(counts['count_1h'], counts['count_6h'], counts['count_24h'])
    
    async def _update_all_term_metrics(self):
        """Update metrics for all tracked terms"""
        
        # Get recent terms from database
        recent_terms = await self._get_recent_terms_from_db()
        
        for term_data in recent_terms:
            normalized_term = term_data['normalized_term']
            
            if normalized_term not in self.trending_terms:
                self.trending_terms[normalized_term] = TrendingTerm(
                    term_data['term'],
                    normalized_term,
                    term_data.get('term_type', 'general')
                )
            
            term_obj = self.trending_terms[normalized_term]
            term_obj.update_counts(
                term_data['count_1h'],
                term_data['count_6h'],
                term_data['count_24h']
            )
            
            # Update related terms and context
            term_obj.related_terms = term_data.get('related_terms', [])
            term_obj.sports_context = term_data.get('sports_context', {})
    
    async def _upsert_term_in_db(self, term: TrendingTerm):
        """Insert or update term in database"""
        
        query = """
        INSERT INTO trending_terms (
            term, normalized_term, term_type, count_1h, count_6h, count_24h,
            burst_ratio, trend_score, is_trending, trend_start, trend_peak,
            last_seen, related_terms, sports_context, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
        ON CONFLICT (normalized_term) DO UPDATE SET
            term = EXCLUDED.term,
            term_type = EXCLUDED.term_type,
            count_1h = EXCLUDED.count_1h,
            count_6h = EXCLUDED.count_6h,
            count_24h = EXCLUDED.count_24h,
            burst_ratio = EXCLUDED.burst_ratio,
            trend_score = EXCLUDED.trend_score,
            is_trending = EXCLUDED.is_trending,
            trend_start = EXCLUDED.trend_start,
            trend_peak = EXCLUDED.trend_peak,
            last_seen = EXCLUDED.last_seen,
            related_terms = EXCLUDED.related_terms,
            sports_context = EXCLUDED.sports_context,
            updated_at = NOW()
        """
        
        await self.pool.execute(
            query,
            term.term,
            term.normalized_term,
            term.term_type,
            term.count_1h,
            term.count_6h,
            term.count_24h,
            term.burst_ratio,
            term.trend_score,
            term.is_trending,
            term.trend_start,
            term.trend_peak,
            term.last_seen,
            term.related_terms,
            term.sports_context
        )
    
    async def _get_term_counts_from_db(self, normalized_term: str) -> Optional[Dict[str, int]]:
        """Get time-windowed counts for a term"""
        
        query = """
        WITH term_occurrences AS (
            SELECT created_at
            FROM content_items ci
            WHERE ci.sports_keywords @> ARRAY[$1]
            AND ci.created_at >= NOW() - INTERVAL '24 hours'
            AND ci.is_active = true
        )
        SELECT 
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as count_1h,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '6 hours') as count_6h,
            COUNT(*) as count_24h
        FROM term_occurrences
        """
        
        result = await self.pool.fetchrow(query, normalized_term)
        
        if result:
            return {
                'count_1h': result['count_1h'],
                'count_6h': result['count_6h'],
                'count_24h': result['count_24h']
            }
        
        return None
    
    async def _get_recent_terms_from_db(self) -> List[Dict[str, Any]]:
        """Get recently active terms from database"""
        
        query = """
        SELECT 
            term, normalized_term, term_type, count_1h, count_6h, count_24h,
            burst_ratio, trend_score, is_trending, related_terms, sports_context,
            last_seen
        FROM trending_terms
        WHERE last_seen >= NOW() - INTERVAL '24 hours'
        ORDER BY trend_score DESC
        LIMIT 1000
        """
        
        rows = await self.pool.fetch(query)
        return [dict(row) for row in rows]
    
    def _is_in_cooldown(self, normalized_term: str) -> bool:
        """Check if term is in cooldown period"""
        
        if normalized_term not in self.cooldown_terms:
            return False
        
        cooldown_until = self.cooldown_terms[normalized_term]
        return datetime.utcnow() < cooldown_until
    
    def _add_to_cooldown(self, normalized_term: str):
        """Add term to cooldown"""
        
        cooldown_until = datetime.utcnow() + timedelta(hours=self.settings.trending.cooldown_hours)
        self.cooldown_terms[normalized_term] = cooldown_until
    
    def _calculate_query_priority(self, term: TrendingTerm) -> float:
        """Calculate priority for discovery query"""
        
        # Base priority from trend score
        priority = term.trend_score
        
        # Boost for high burst ratio
        if term.burst_ratio > 5.0:
            priority *= 1.5
        
        # Boost for sports-specific terms
        if term.term_type in ['teams', 'players', 'events']:
            priority *= 1.3
        
        # Boost for recent activity
        hours_since_peak = 0
        if term.trend_peak:
            hours_since_peak = (datetime.utcnow() - term.trend_peak).total_seconds() / 3600
        
        if hours_since_peak < 1:
            priority *= 1.4
        elif hours_since_peak < 6:
            priority *= 1.2
        
        return min(1.0, priority)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trending detection statistics"""
        
        stats = self.stats.copy()
        stats['active_terms'] = len(self.trending_terms)
        stats['cooldown_terms'] = len(self.cooldown_terms)
        
        # Current trending terms
        current_trending = [
            term.to_dict() for term in self.trending_terms.values()
            if term.is_trending
        ]
        stats['current_trending'] = current_trending
        
        return stats


# Trending discovery integration
class TrendingDiscoveryLoop:
    """Integrates trending detection with content discovery"""
    
    def __init__(self, settings: Settings, connection_pool: ConnectionPool):
        self.settings = settings
        self.detector = TrendingDetector(settings, connection_pool)
        self.discovery_queue = []  # Would integrate with actual discovery system
    
    async def run_detection_cycle(self) -> Dict[str, Any]:
        """Run one cycle of trending detection and query generation"""
        
        # Detect trending terms
        trending_terms = await self.detector.detect_trending()
        
        # Generate discovery queries
        discovery_queries = await self.detector.generate_discovery_queries(trending_terms)
        
        # Add to discovery queue (in production, this would trigger actual discovery)
        self.discovery_queue.extend(discovery_queries)
        
        # Keep queue size manageable
        if len(self.discovery_queue) > 1000:
            self.discovery_queue = self.discovery_queue[-1000:]
        
        return {
            'trending_terms_count': len(trending_terms),
            'discovery_queries_count': len(discovery_queries),
            'queue_size': len(self.discovery_queue),
            'trending_terms': [term.to_dict() for term in trending_terms[:10]],  # Top 10
            'sample_queries': discovery_queries[:5],  # Sample queries
            'stats': self.detector.get_stats()
        }
    
    async def process_new_content(self, content: Dict[str, Any]) -> List[str]:
        """Process new content for trending term extraction"""
        
        return await self.detector.process_content(content)
    
    def get_pending_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending discovery queries"""
        
        # Sort by priority and return top queries
        sorted_queries = sorted(
            self.discovery_queue,
            key=lambda q: q['priority'],
            reverse=True
        )
        
        return sorted_queries[:limit]
    
    def mark_queries_processed(self, query_ids: List[str]):
        """Mark queries as processed (remove from queue)"""
        
        # In production, this would track query IDs
        # For now, just clear processed queries
        pass


# Example usage
async def main():
    """Example trending detection usage"""
    
    from libs.common.config import Settings
    from libs.common.database import ConnectionPool
    
    settings = get_settings()
    
    # Initialize connection pool
    pool = ConnectionPool(settings.database.url)
    await pool.initialize()
    
    # Initialize trending loop
    trending_loop = TrendingDiscoveryLoop(settings, pool)
    
    try:
        # Example content processing
        content = {
            'title': 'Lakers Trade Rumors: Russell Westbrook Deal Latest News',
            'text': 'The Los Angeles Lakers are reportedly exploring trade options for Russell Westbrook as the NBA trade deadline approaches. Sources indicate multiple teams have shown interest in acquiring the former MVP.',
            'sports_keywords': ['Lakers', 'Russell Westbrook', 'NBA', 'trade', 'deadline']
        }
        
        # Process content
        extracted_terms = await trending_loop.process_new_content(content)
        print(f"Extracted terms: {extracted_terms}")
        
        # Run detection cycle
        cycle_result = await trending_loop.run_detection_cycle()
        print(f"Detection cycle result: {cycle_result}")
        
        # Get pending queries
        pending_queries = trending_loop.get_pending_queries(10)
        print(f"Pending queries: {len(pending_queries)}")
        
        for query in pending_queries[:3]:
            print(f"  Query: {query['query']} (priority: {query['priority']:.3f})")
    
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())

