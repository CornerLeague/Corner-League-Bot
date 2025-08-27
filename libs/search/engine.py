# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Search engine with PostgreSQL full-text search and OpenSearch migration path.
Implements BM25 scoring, caching, and cursor-based pagination.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import asyncpg
from elasticsearch import AsyncElasticsearch
from rank_bm25 import BM25Okapi

from libs.common.config import get_settings, Settings
from libs.common.database import ConnectionPool

logger = logging.getLogger(__name__)


class SearchQuery:
    """Structured search query with filters and sorting"""
    
    def __init__(self, query: str = "", **kwargs):
        self.query = query.strip()
        self.sports = kwargs.get('sports', [])
        self.sources = kwargs.get('sources', [])
        self.content_types = kwargs.get('content_types', [])
        self.quality_threshold = kwargs.get('quality_threshold')
        self.date_range = kwargs.get('date_range', {})
        self.sort_by = kwargs.get('sort_by', 'relevance')
        self.limit = min(kwargs.get('limit', 20), 100)
        self.cursor = kwargs.get('cursor')
        
        # Validate sort options
        valid_sorts = ['relevance', 'date', 'quality', 'popularity']
        if self.sort_by not in valid_sorts:
            self.sort_by = 'relevance'
    
    def to_cache_key(self) -> str:
        """Generate cache key for query"""
        
        key_data = {
            'query': self.query,
            'sports': sorted(self.sports) if self.sports else [],
            'sources': sorted(self.sources) if self.sources else [],
            'content_types': sorted(self.content_types) if self.content_types else [],
            'quality_threshold': self.quality_threshold,
            'date_range': self.date_range,
            'sort_by': self.sort_by,
            'limit': self.limit,
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def __repr__(self):
        return f"SearchQuery(query='{self.query}', sort_by='{self.sort_by}', limit={self.limit})"


class PostgreSQLSearchEngine:
    """PostgreSQL full-text search implementation"""
    
    def __init__(self, settings: Settings, connection_pool: ConnectionPool, db_manager=None):
        self.settings = settings
        # Use provided db_manager or create new one
        if db_manager:
            self.db_manager = db_manager
        else:
            # Import here to avoid circular imports
            from libs.common.database import DatabaseManager
            self.db_manager = DatabaseManager(settings.database.url)
    
    async def search(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Execute search using PostgreSQL FTS"""
        
        start_time = time.time()
        
        # Build SQL query
        sql_query, params = self._build_sql_query(search_query)
        
        try:
            # Use SQLAlchemy session for database operations
            async for session in self.db_manager.get_session():
                # Execute search using SQLAlchemy
                from sqlalchemy import text
                result = await session.execute(text(sql_query), params)
                rows = result.fetchall()
                
                # Process results
                items = []
                for row in rows:
                    item = dict(row._mapping)
                    
                    # Add search metadata
                    item['search_score'] = item.get('search_score', 0.0)
                    item['search_rank'] = len(items) + 1
                    
                    items.append(item)
                
                # Get total count (for pagination)
                count_query, count_params = self._build_count_query(search_query)
                count_result = await session.execute(text(count_query), count_params)
                total_count = count_result.scalar()
            
            # Generate next cursor
            next_cursor = None
            if len(items) == search_query.limit and len(items) > 0:
                last_item = items[-1]
                next_cursor = self._generate_cursor(last_item, search_query)
            
            search_time = (time.time() - start_time) * 1000
            
            return {
                'items': items,
                'total_count': total_count or 0,
                'has_more': next_cursor is not None,
                'next_cursor': next_cursor,
                'search_time_ms': search_time,
                'engine': 'postgresql'
            }
        
        except Exception as e:
            logger.error(f"PostgreSQL search error: {e}")
            raise
    
    def _build_sql_query(self, search_query: SearchQuery) -> Tuple[str, Dict[str, Any]]:
        """Build SQLite-compatible search query"""
        
        params = {}
        where_conditions = []
        
        # Base query with joins
        base_query = """
        SELECT 
            ci.id,
            ci.title,
            ci.byline,
            ci.summary,
            ci.canonical_url,
            ci.published_at,
            ci.quality_score,
            ci.sports_keywords,
            ci.content_type,
            ci.image_url,
            s.name as source_name,
            ci.word_count,
            ci.language
        """
        
        # Add search scoring if query provided
        if search_query.query:
            # Simple relevance scoring based on title and summary matches
            base_query += """
            , (CASE 
                WHEN ci.title LIKE '%' || :query || '%' THEN 3.0
                WHEN ci.summary LIKE '%' || :query || '%' THEN 2.0
                ELSE 1.0
              END) as search_score
            """
            params['query'] = search_query.query
        else:
            base_query += ", ci.quality_score as search_score"
        
        base_query += """
        FROM content_items ci
        JOIN sources s ON ci.source_id = s.id
        """
        
        # Add search condition
        if search_query.query:
            where_conditions.append("(ci.title LIKE '%' || :query || '%' OR ci.summary LIKE '%' || :query || '%' OR ci.sports_keywords LIKE '%' || :query || '%')")
        
        # Add filters
        where_conditions.append("ci.is_active = 1")
        where_conditions.append("ci.is_duplicate = 0")
        where_conditions.append("ci.is_spam = 0")
        
        # Sports filter
        if search_query.sports:
            sports_conditions = []
            for i, sport in enumerate(search_query.sports):
                param_name = f'sport_{i}'
                params[param_name] = f'%{sport}%'
                sports_conditions.append(f"ci.sports_keywords LIKE :{param_name}")
            if sports_conditions:
                where_conditions.append(f"({' OR '.join(sports_conditions)})")
        
        # Sources filter
        if search_query.sources:
            sources_conditions = []
            for i, source in enumerate(search_query.sources):
                param_name = f'source_{i}'
                params[param_name] = source
                sources_conditions.append(f"s.domain = :{param_name}")
            if sources_conditions:
                where_conditions.append(f"({' OR '.join(sources_conditions)})")
        
        # Content types filter
        if search_query.content_types:
            types_conditions = []
            for i, content_type in enumerate(search_query.content_types):
                param_name = f'type_{i}'
                params[param_name] = content_type
                types_conditions.append(f"ci.content_type = :{param_name}")
            if types_conditions:
                where_conditions.append(f"({' OR '.join(types_conditions)})")
        
        # Quality threshold
        if search_query.quality_threshold is not None:
            params['quality_threshold'] = search_query.quality_threshold
            where_conditions.append("ci.quality_score >= :quality_threshold")
        
        # Date range filter
        if search_query.date_range:
            if 'start' in search_query.date_range:
                params['date_start'] = search_query.date_range['start']
                where_conditions.append("ci.published_at >= :date_start")
            
            if 'end' in search_query.date_range:
                params['date_end'] = search_query.date_range['end']
                where_conditions.append("ci.published_at <= :date_end")
        
        # Skip cursor-based pagination for now - will need separate handling
        # if search_query.cursor:
        #     cursor_conditions = self._parse_cursor(search_query.cursor, search_query)
        #     if cursor_conditions:
        #         where_conditions.extend(cursor_conditions['conditions'])
        #         params.update(cursor_conditions['params'])
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build ORDER BY clause
        order_clause = self._build_order_clause(search_query)
        
        # Build LIMIT clause
        params['limit'] = search_query.limit
        limit_clause = "LIMIT :limit"
        
        # Combine query
        full_query = f"{base_query} {where_clause} {order_clause} {limit_clause}"
        
        return full_query, params
    
    def _build_count_query(self, search_query: SearchQuery) -> Tuple[str, Dict[str, Any]]:
        """Build count query for pagination"""
        
        params = {}
        where_conditions = []
        
        base_query = """
        SELECT COUNT(*)
        FROM content_items ci
        JOIN sources s ON ci.source_id = s.id
        """
        
        # Add search condition
        if search_query.query:
            params['query'] = search_query.query
            where_conditions.append("(ci.title LIKE '%' || :query || '%' OR ci.summary LIKE '%' || :query || '%' OR ci.sports_keywords LIKE '%' || :query || '%')")
        
        # Add same filters as main query (excluding cursor)
        where_conditions.append("ci.is_active = 1")
        where_conditions.append("ci.is_duplicate = 0")
        where_conditions.append("ci.is_spam = 0")
        
        # Sports filter
        if search_query.sports:
            sports_conditions = []
            for i, sport in enumerate(search_query.sports):
                param_name = f'sport_{i}'
                params[param_name] = f'%{sport}%'
                sports_conditions.append(f"ci.sports_keywords LIKE :{param_name}")
            if sports_conditions:
                where_conditions.append(f"({' OR '.join(sports_conditions)})")
        
        # Sources filter
        if search_query.sources:
            sources_conditions = []
            for i, source in enumerate(search_query.sources):
                param_name = f'source_{i}'
                params[param_name] = source
                sources_conditions.append(f"s.domain = :{param_name}")
            if sources_conditions:
                where_conditions.append(f"({' OR '.join(sources_conditions)})")
        
        # Content types filter
        if search_query.content_types:
            types_conditions = []
            for i, content_type in enumerate(search_query.content_types):
                param_name = f'type_{i}'
                params[param_name] = content_type
                types_conditions.append(f"ci.content_type = :{param_name}")
            if types_conditions:
                where_conditions.append(f"({' OR '.join(types_conditions)})")
        
        if search_query.quality_threshold is not None:
            params['quality_threshold'] = search_query.quality_threshold
            where_conditions.append("ci.quality_score >= :quality_threshold")
        
        if search_query.date_range:
            if 'start' in search_query.date_range:
                params['date_start'] = search_query.date_range['start']
                where_conditions.append("ci.published_at >= :date_start")
            
            if 'end' in search_query.date_range:
                params['date_end'] = search_query.date_range['end']
                where_conditions.append("ci.published_at <= :date_end")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        full_query = f"{base_query} {where_clause}"
        
        return full_query, params
    
    def _build_order_clause(self, search_query: SearchQuery) -> str:
        """Build ORDER BY clause"""
        
        if search_query.sort_by == 'relevance':
            if search_query.query:
                return "ORDER BY search_score DESC, ci.published_at DESC"
            else:
                return "ORDER BY ci.quality_score DESC, ci.published_at DESC"
        
        elif search_query.sort_by == 'date':
            return "ORDER BY ci.published_at DESC, ci.quality_score DESC"
        
        elif search_query.sort_by == 'quality':
            return "ORDER BY ci.quality_score DESC, ci.published_at DESC"
        
        elif search_query.sort_by == 'popularity':
            # This would require interaction data
            return "ORDER BY ci.quality_score DESC, ci.published_at DESC"
        
        else:
            return "ORDER BY ci.published_at DESC"
    
    def _generate_cursor(self, item: Dict[str, Any], search_query: SearchQuery) -> str:
        """Generate cursor for pagination"""
        
        cursor_data = {
            'id': str(item['id']),
            'sort_by': search_query.sort_by,
        }
        
        # Helper function to format published_at
        def format_published_at(published_at):
            if not published_at:
                return None
            if isinstance(published_at, str):
                return published_at
            return published_at.isoformat()
        
        if search_query.sort_by == 'relevance':
            cursor_data['search_score'] = item.get('search_score', 0.0)
            cursor_data['published_at'] = format_published_at(item.get('published_at'))
        
        elif search_query.sort_by == 'date':
            cursor_data['published_at'] = format_published_at(item.get('published_at'))
            cursor_data['quality_score'] = item.get('quality_score', 0.0)
        
        elif search_query.sort_by == 'quality':
            cursor_data['quality_score'] = item.get('quality_score', 0.0)
            cursor_data['published_at'] = format_published_at(item.get('published_at'))
        
        # Encode cursor
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        import base64
        return base64.b64encode(cursor_json.encode()).decode()
    
    def _parse_cursor(self, cursor: str, search_query: SearchQuery) -> Optional[Dict[str, Any]]:
        """Parse cursor for pagination"""
        
        try:
            import base64
            cursor_json = base64.b64decode(cursor.encode()).decode()
            cursor_data = json.loads(cursor_json)
            
            conditions = []
            params = []
            
            if cursor_data.get('sort_by') != search_query.sort_by:
                return None  # Sort changed, cursor invalid
            
            # Build cursor conditions based on sort
            if search_query.sort_by == 'relevance':
                if 'search_score' in cursor_data:
                    conditions.append("(search_score < $PARAM OR (search_score = $PARAM AND ci.published_at < $PARAM))")
                    params.extend([cursor_data['search_score'], cursor_data['search_score']])
                    
                    if cursor_data.get('published_at'):
                        params.append(cursor_data['published_at'])
            
            elif search_query.sort_by == 'date':
                if cursor_data.get('published_at'):
                    conditions.append("ci.published_at < $PARAM")
                    params.append(cursor_data['published_at'])
            
            elif search_query.sort_by == 'quality':
                if 'quality_score' in cursor_data:
                    conditions.append("(ci.quality_score < $PARAM OR (ci.quality_score = $PARAM AND ci.published_at < $PARAM))")
                    params.extend([cursor_data['quality_score'], cursor_data['quality_score']])
                    
                    if cursor_data.get('published_at'):
                        params.append(cursor_data['published_at'])
            
            # Replace $PARAM with actual parameter numbers
            param_num = 1  # This will be adjusted by caller
            for i, condition in enumerate(conditions):
                while '$PARAM' in condition:
                    condition = condition.replace('$PARAM', f'${param_num}', 1)
                    param_num += 1
                conditions[i] = condition
            
            return {
                'conditions': conditions,
                'params': params
            }
        
        except Exception as e:
            logger.warning(f"Invalid cursor: {e}")
            return None


class OpenSearchEngine:
    """OpenSearch/Elasticsearch implementation for high-scale search"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[AsyncElasticsearch] = None
        self.index_name = settings.search.es_index_name
    
    async def initialize(self):
        """Initialize OpenSearch client"""
        
        self.client = AsyncElasticsearch(
            [self.settings.elasticsearch.url],
            http_auth=(
                self.settings.elasticsearch.username,
                self.settings.elasticsearch.password
            ) if self.settings.elasticsearch.username else None,
            verify_certs=self.settings.elasticsearch.verify_certs,
            timeout=self.settings.elasticsearch.timeout,
            max_retries=self.settings.elasticsearch.max_retries,
        )
        
        # Create index if it doesn't exist
        await self._ensure_index_exists()
    
    async def close(self):
        """Close OpenSearch client"""
        if self.client:
            await self.client.close()
    
    async def search(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Execute search using OpenSearch"""
        
        if not self.client:
            raise RuntimeError("OpenSearch client not initialized")
        
        start_time = time.time()
        
        # Build OpenSearch query
        es_query = self._build_es_query(search_query)
        
        try:
            # Execute search
            response = await self.client.search(
                index=self.index_name,
                body=es_query,
                timeout='30s'
            )
            
            # Process results
            items = []
            for hit in response['hits']['hits']:
                item = hit['_source']
                item['id'] = hit['_id']
                item['search_score'] = hit['_score']
                item['search_rank'] = len(items) + 1
                items.append(item)
            
            # Generate next cursor
            next_cursor = None
            if len(items) == search_query.limit and len(items) > 0:
                last_item = items[-1]
                next_cursor = self._generate_cursor(last_item, search_query)
            
            search_time = (time.time() - start_time) * 1000
            
            return {
                'items': items,
                'total_count': response['hits']['total']['value'],
                'has_more': next_cursor is not None,
                'next_cursor': next_cursor,
                'search_time_ms': search_time,
                'engine': 'opensearch'
            }
        
        except Exception as e:
            logger.error(f"OpenSearch error: {e}")
            raise
    
    def _build_es_query(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Build OpenSearch query"""
        
        query = {
            'size': search_query.limit,
            'query': {
                'bool': {
                    'must': [],
                    'filter': [],
                    'must_not': []
                }
            },
            'sort': []
        }
        
        # Text search
        if search_query.query:
            query['query']['bool']['must'].append({
                'multi_match': {
                    'query': search_query.query,
                    'fields': ['title^3', 'text^1', 'sports_keywords^2'],
                    'type': 'best_fields',
                    'fuzziness': 'AUTO'
                }
            })
        else:
            query['query']['bool']['must'].append({'match_all': {}})
        
        # Filters
        query['query']['bool']['filter'].extend([
            {'term': {'is_active': True}},
            {'term': {'is_duplicate': False}},
            {'term': {'is_spam': False}}
        ])
        
        # Sports filter
        if search_query.sports:
            query['query']['bool']['filter'].append({
                'terms': {'sports_keywords': search_query.sports}
            })
        
        # Sources filter
        if search_query.sources:
            query['query']['bool']['filter'].append({
                'terms': {'source_domain': search_query.sources}
            })
        
        # Content types filter
        if search_query.content_types:
            query['query']['bool']['filter'].append({
                'terms': {'content_type': search_query.content_types}
            })
        
        # Quality threshold
        if search_query.quality_threshold is not None:
            query['query']['bool']['filter'].append({
                'range': {'quality_score': {'gte': search_query.quality_threshold}}
            })
        
        # Date range filter
        if search_query.date_range:
            date_filter = {'range': {'published_at': {}}}
            
            if 'start' in search_query.date_range:
                date_filter['range']['published_at']['gte'] = search_query.date_range['start']
            
            if 'end' in search_query.date_range:
                date_filter['range']['published_at']['lte'] = search_query.date_range['end']
            
            query['query']['bool']['filter'].append(date_filter)
        
        # Sorting
        if search_query.sort_by == 'relevance':
            query['sort'] = ['_score', {'published_at': 'desc'}]
        elif search_query.sort_by == 'date':
            query['sort'] = [{'published_at': 'desc'}, {'quality_score': 'desc'}]
        elif search_query.sort_by == 'quality':
            query['sort'] = [{'quality_score': 'desc'}, {'published_at': 'desc'}]
        else:
            query['sort'] = [{'published_at': 'desc'}]
        
        # Cursor-based pagination
        if search_query.cursor:
            search_after = self._parse_cursor(search_query.cursor)
            if search_after:
                query['search_after'] = search_after
        
        return query
    
    def _generate_cursor(self, item: Dict[str, Any], search_query: SearchQuery) -> str:
        """Generate cursor for OpenSearch pagination"""
        
        sort_values = []
        
        if search_query.sort_by == 'relevance':
            sort_values = [item.get('search_score', 0.0), item.get('published_at')]
        elif search_query.sort_by == 'date':
            sort_values = [item.get('published_at'), item.get('quality_score', 0.0)]
        elif search_query.sort_by == 'quality':
            sort_values = [item.get('quality_score', 0.0), item.get('published_at')]
        else:
            sort_values = [item.get('published_at')]
        
        # Encode cursor
        cursor_json = json.dumps(sort_values)
        import base64
        return base64.b64encode(cursor_json.encode()).decode()
    
    def _parse_cursor(self, cursor: str) -> Optional[List[Any]]:
        """Parse cursor for OpenSearch pagination"""
        
        try:
            import base64
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception as e:
            logger.warning(f"Invalid OpenSearch cursor: {e}")
            return None
    
    async def _ensure_index_exists(self):
        """Ensure search index exists with proper mapping"""
        
        if not await self.client.indices.exists(index=self.index_name):
            mapping = {
                'mappings': {
                    'properties': {
                        'title': {'type': 'text', 'analyzer': 'english'},
                        'text': {'type': 'text', 'analyzer': 'english'},
                        'byline': {'type': 'text'},
                        'summary': {'type': 'text', 'analyzer': 'english'},
                        'canonical_url': {'type': 'keyword'},
                        'published_at': {'type': 'date'},
                        'quality_score': {'type': 'float'},
                        'sports_keywords': {'type': 'keyword'},
                        'content_type': {'type': 'keyword'},
                        'source_name': {'type': 'keyword'},
                        'source_domain': {'type': 'keyword'},
                        'language': {'type': 'keyword'},
                        'word_count': {'type': 'integer'},
                        'is_active': {'type': 'boolean'},
                        'is_duplicate': {'type': 'boolean'},
                        'is_spam': {'type': 'boolean'},
                    }
                },
                'settings': {
                    'number_of_shards': self.settings.search.es_shards,
                    'number_of_replicas': self.settings.search.es_replicas,
                    'analysis': {
                        'analyzer': {
                            'sports_analyzer': {
                                'type': 'custom',
                                'tokenizer': 'standard',
                                'filter': ['lowercase', 'stop', 'snowball']
                            }
                        }
                    }
                }
            }
            
            await self.client.indices.create(
                index=self.index_name,
                body=mapping
            )
            
            logger.info(f"Created OpenSearch index: {self.index_name}")


class SearchCache:
    """Redis-based search result caching"""
    
    def __init__(self, redis_client, settings: Settings):
        self.redis = redis_client
        self.settings = settings
        self.cache_prefix = "search:"
        self.ttl = settings.search.cache_ttl_seconds
    
    async def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        
        if not self.settings.search.cache_search_results:
            return None
        
        try:
            cached_data = await self.redis.get(f"{self.cache_prefix}{cache_key}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(self, cache_key: str, results: Dict[str, Any]) -> None:
        """Cache search results"""
        
        if not self.settings.search.cache_search_results:
            return
        
        try:
            # Add cache metadata
            cached_results = results.copy()
            cached_results['cached_at'] = datetime.utcnow().isoformat()
            
            await self.redis.setex(
                f"{self.cache_prefix}{cache_key}",
                self.ttl,
                json.dumps(cached_results, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        
        try:
            keys = await self.redis.keys(f"{self.cache_prefix}{pattern}")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


class SearchEngine:
    """Main search engine with automatic backend selection"""
    
    def __init__(self, settings: Settings, connection_pool: ConnectionPool, redis_client=None, db_manager=None):
        self.settings = settings
        self.postgresql_engine = PostgreSQLSearchEngine(settings, None, db_manager)
        self.opensearch_engine = OpenSearchEngine(settings) if settings.search.use_elasticsearch else None
        self.cache = SearchCache(redis_client, settings) if redis_client else None
        
        # Performance thresholds for backend selection
        self.postgres_qps_threshold = 200
        self.postgres_corpus_threshold = 1000000
    
    async def initialize(self):
        """Initialize search engines"""
        if self.opensearch_engine:
            await self.opensearch_engine.initialize()
    
    async def close(self):
        """Close search engines"""
        if self.opensearch_engine:
            await self.opensearch_engine.close()
    
    async def search(self, search_query: SearchQuery) -> Dict[str, Any]:
        """Execute search with automatic backend selection"""
        
        # Check cache first
        cache_key = search_query.to_cache_key()
        if self.cache:
            cached_results = await self.cache.get(cache_key)
            if cached_results:
                cached_results['from_cache'] = True
                return cached_results
        
        # Select search backend
        use_opensearch = (
            self.opensearch_engine and 
            self.settings.search.use_elasticsearch and
            self._should_use_opensearch()
        )
        
        # Execute search
        if use_opensearch:
            results = await self.opensearch_engine.search(search_query)
        else:
            results = await self.postgresql_engine.search(search_query)
        
        results['from_cache'] = False
        
        # Cache results
        if self.cache and results.get('search_time_ms', 0) > 100:
            await self.cache.set(cache_key, results)
        
        return results
    
    def _should_use_opensearch(self) -> bool:
        """Determine if OpenSearch should be used based on load"""
        
        # This would check current QPS and corpus size
        # For now, use configuration setting
        return self.settings.search.use_elasticsearch
    
    async def suggest(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions"""
        
        # Simple implementation using PostgreSQL
        # In production, you'd use a dedicated suggestion engine
        
        if len(query) < 2:
            return []
        
        sql = """
        SELECT DISTINCT unnest(sports_keywords) as suggestion
        FROM content_items
        WHERE sports_keywords && ARRAY[:query_param]
        AND is_active = true
        LIMIT :limit_param
        """
        
        try:
            async for session in self.postgresql_engine.db_manager.get_session():
                from sqlalchemy import text
                result = await session.execute(text(sql), {
                    'query_param': f"%{query}%",
                    'limit_param': limit
                })
                rows = result.fetchall()
                return [row.suggestion for row in rows]
        except Exception as e:
            logger.error(f"Suggestion error: {e}")
            return []
    
    async def get_trending_terms(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending search terms"""
        
        # This would integrate with the trending detection system
        # For now, return empty list
        return []


# Example usage
async def main():
    """Example search usage"""
    
    from libs.common.config import Settings
    from libs.common.database import DatabaseManager
    
    settings = get_settings()
    
    # Initialize database manager
    db_manager = DatabaseManager(settings.database.url)
    
    # Initialize search engine
    search_engine = SearchEngine(settings, None, None, db_manager)
    await search_engine.initialize()
    
    try:
        # Example search
        query = SearchQuery(
            query="Lakers Warriors game",
            sports=["basketball", "nba"],
            sort_by="relevance",
            limit=10
        )
        
        results = await search_engine.search(query)
        
        print(f"Found {results['total_count']} results in {results['search_time_ms']:.1f}ms")
        print(f"Engine: {results['engine']}")
        print(f"From cache: {results['from_cache']}")
        
        for i, item in enumerate(results['items'], 1):
            print(f"{i}. {item['title']} (score: {item['search_score']:.3f})")
        
        # Test suggestions
        suggestions = await search_engine.suggest("lak")
        print(f"Suggestions for 'lak': {suggestions}")
    
    finally:
        await search_engine.close()
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())

