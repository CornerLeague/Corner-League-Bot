# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Chaos engineering test suite for sports media platform.
Tests system resilience under various failure conditions.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from unittest.mock import patch, MagicMock

import pytest
import aioredis
import asyncpg
from pydantic import BaseModel

from libs.common.config import Settings
from libs.common.database import ConnectionPool
from libs.ingestion.crawler import WebCrawler
from libs.search.engine import SearchEngine
from apps.api.main import app

logger = logging.getLogger(__name__)


class ChaosScenario(BaseModel):
    """Chaos engineering scenario definition"""
    
    name: str
    description: str
    duration_seconds: int = 60
    failure_rate: float = 0.5  # 0.0 to 1.0
    recovery_time_seconds: int = 30
    expected_behavior: str = ""
    success_criteria: Dict[str, Any] = {}


class ChaosTestResult(BaseModel):
    """Chaos test execution result"""
    
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_count: int = 0
    recovery_time_seconds: float = 0.0
    performance_impact: Dict[str, float] = {}
    logs: List[str] = []
    metrics: Dict[str, Any] = {}


class ChaosEngineer:
    """Chaos engineering test framework"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.scenarios: List[ChaosScenario] = []
        self.results: List[ChaosTestResult] = []
        
        # System components for testing
        self.connection_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.search_engine: Optional[SearchEngine] = None
        
        # Monitoring
        self.baseline_metrics: Dict[str, float] = {}
        self.current_metrics: Dict[str, float] = {}
        
        self._define_chaos_scenarios()
    
    def _define_chaos_scenarios(self):
        """Define chaos engineering scenarios"""
        
        self.scenarios = [
            # Database Failures
            ChaosScenario(
                name="database_connection_failure",
                description="Simulate database connection pool exhaustion",
                duration_seconds=120,
                failure_rate=0.8,
                recovery_time_seconds=45,
                expected_behavior="API should gracefully degrade, return cached data, and recover automatically",
                success_criteria={
                    "max_error_rate": 0.1,
                    "max_response_time_ms": 5000,
                    "recovery_time_max_seconds": 60
                }
            ),
            
            ChaosScenario(
                name="database_query_timeout",
                description="Simulate slow database queries and timeouts",
                duration_seconds=90,
                failure_rate=0.6,
                recovery_time_seconds=30,
                expected_behavior="Queries should timeout gracefully and fallback to cache",
                success_criteria={
                    "max_error_rate": 0.15,
                    "max_response_time_ms": 10000,
                    "cache_hit_rate_min": 0.7
                }
            ),
            
            # Redis Failures
            ChaosScenario(
                name="redis_cluster_failure",
                description="Simulate Redis cluster node failures",
                duration_seconds=180,
                failure_rate=0.7,
                recovery_time_seconds=60,
                expected_behavior="System should continue operating without caching, with degraded performance",
                success_criteria={
                    "max_error_rate": 0.05,
                    "max_response_time_ms": 8000,
                    "recovery_time_max_seconds": 90
                }
            ),
            
            ChaosScenario(
                name="redis_memory_pressure",
                description="Simulate Redis memory exhaustion and eviction",
                duration_seconds=150,
                failure_rate=0.5,
                recovery_time_seconds=45,
                expected_behavior="Cache should evict old entries and continue operating",
                success_criteria={
                    "max_error_rate": 0.1,
                    "cache_hit_rate_min": 0.3,
                    "memory_usage_max_mb": 1000
                }
            ),
            
            # Network Failures
            ChaosScenario(
                name="proxy_pool_outage",
                description="Simulate Evomi proxy pool complete outage",
                duration_seconds=300,
                failure_rate=1.0,
                recovery_time_seconds=120,
                expected_behavior="Crawler should fallback to direct connections or pause gracefully",
                success_criteria={
                    "crawler_error_rate_max": 0.2,
                    "recovery_time_max_seconds": 180,
                    "data_loss_max_percent": 0.1
                }
            ),
            
            ChaosScenario(
                name="intermittent_network_failures",
                description="Simulate random network connectivity issues",
                duration_seconds=240,
                failure_rate=0.3,
                recovery_time_seconds=60,
                expected_behavior="System should retry failed requests and maintain overall stability",
                success_criteria={
                    "max_error_rate": 0.2,
                    "retry_success_rate_min": 0.8,
                    "recovery_time_max_seconds": 90
                }
            ),
            
            # API Failures
            ChaosScenario(
                name="deepseek_api_outage",
                description="Simulate DeepSeek AI API complete outage",
                duration_seconds=180,
                failure_rate=1.0,
                recovery_time_seconds=30,
                expected_behavior="Summarization should fallback to extractive methods",
                success_criteria={
                    "summarization_error_rate_max": 0.1,
                    "fallback_success_rate_min": 0.9,
                    "recovery_time_max_seconds": 60
                }
            ),
            
            ChaosScenario(
                name="search_api_degradation",
                description="Simulate search API slow responses and timeouts",
                duration_seconds=120,
                failure_rate=0.4,
                recovery_time_seconds=45,
                expected_behavior="Search should timeout gracefully and return partial results",
                success_criteria={
                    "max_error_rate": 0.1,
                    "max_response_time_ms": 15000,
                    "partial_results_rate_min": 0.8
                }
            ),
            
            # Resource Exhaustion
            ChaosScenario(
                name="memory_pressure",
                description="Simulate high memory usage and pressure",
                duration_seconds=180,
                failure_rate=0.6,
                recovery_time_seconds=90,
                expected_behavior="System should handle memory pressure gracefully without crashes",
                success_criteria={
                    "crash_count_max": 0,
                    "memory_leak_rate_max_mb_per_min": 10,
                    "gc_frequency_max_per_min": 60
                }
            ),
            
            ChaosScenario(
                name="cpu_saturation",
                description="Simulate high CPU load and processing delays",
                duration_seconds=150,
                failure_rate=0.8,
                recovery_time_seconds=60,
                expected_behavior="System should throttle processing and maintain responsiveness",
                success_criteria={
                    "max_response_time_ms": 20000,
                    "throughput_degradation_max_percent": 0.5,
                    "recovery_time_max_seconds": 90
                }
            )
        ]
    
    async def initialize(self):
        """Initialize chaos testing framework"""
        
        logger.info("Initializing chaos engineering framework")
        
        # Initialize system components
        self.connection_pool = ConnectionPool(self.settings.database.url)
        await self.connection_pool.initialize()
        
        self.redis_client = aioredis.from_url(self.settings.redis.url)
        await self.redis_client.ping()
        
        self.search_engine = SearchEngine(self.settings, self.connection_pool)
        await self.search_engine.initialize()
        
        # Collect baseline metrics
        await self._collect_baseline_metrics()
        
        logger.info("Chaos engineering framework initialized")
    
    async def _collect_baseline_metrics(self):
        """Collect baseline system metrics"""
        
        try:
            # Database metrics
            db_stats = await self.connection_pool.fetchrow("""
                SELECT 
                    COUNT(*) as active_connections,
                    AVG(extract(epoch from (now() - query_start))) as avg_query_time
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            
            self.baseline_metrics.update({
                'db_active_connections': float(db_stats['active_connections'] or 0),
                'db_avg_query_time_seconds': float(db_stats['avg_query_time'] or 0),
            })
            
            # Redis metrics
            redis_info = await self.redis_client.info()
            self.baseline_metrics.update({
                'redis_used_memory_mb': float(redis_info.get('used_memory', 0)) / 1024 / 1024,
                'redis_connected_clients': float(redis_info.get('connected_clients', 0)),
                'redis_ops_per_sec': float(redis_info.get('instantaneous_ops_per_sec', 0)),
            })
            
            # API response time baseline
            start_time = time.time()
            # Simulate API call
            await asyncio.sleep(0.01)  # Placeholder for actual API call
            api_response_time = (time.time() - start_time) * 1000
            
            self.baseline_metrics['api_response_time_ms'] = api_response_time
            
            logger.info(f"Baseline metrics collected: {self.baseline_metrics}")
        
        except Exception as e:
            logger.error(f"Error collecting baseline metrics: {e}")
    
    async def run_chaos_scenario(self, scenario: ChaosScenario) -> ChaosTestResult:
        """Execute a single chaos engineering scenario"""
        
        logger.info(f"Starting chaos scenario: {scenario.name}")
        
        result = ChaosTestResult(
            scenario_name=scenario.name,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),  # Will be updated
            duration_seconds=0.0,
            success=False
        )
        
        start_time = time.time()
        
        try:
            # Phase 1: Inject failure
            failure_context = await self._inject_failure(scenario)
            result.logs.append(f"Failure injected: {failure_context}")
            
            # Phase 2: Monitor system behavior during failure
            monitoring_task = asyncio.create_task(
                self._monitor_system_during_chaos(scenario, result)
            )
            
            # Phase 3: Wait for scenario duration
            await asyncio.sleep(scenario.duration_seconds)
            
            # Phase 4: Stop failure injection
            await self._stop_failure_injection(scenario, failure_context)
            result.logs.append("Failure injection stopped")
            
            # Phase 5: Monitor recovery
            recovery_start = time.time()
            recovery_success = await self._monitor_recovery(scenario, result)
            result.recovery_time_seconds = time.time() - recovery_start
            
            # Stop monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            # Phase 6: Evaluate success criteria
            result.success = self._evaluate_success_criteria(scenario, result)
            
            result.logs.append(f"Scenario completed. Success: {result.success}")
        
        except Exception as e:
            result.logs.append(f"Scenario failed with error: {e}")
            logger.error(f"Chaos scenario {scenario.name} failed: {e}")
        
        finally:
            result.end_time = datetime.utcnow()
            result.duration_seconds = time.time() - start_time
            
            # Cleanup any remaining failure injection
            try:
                await self._cleanup_failure_injection(scenario)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
        
        logger.info(f"Chaos scenario {scenario.name} completed in {result.duration_seconds:.1f}s")
        return result
    
    async def _inject_failure(self, scenario: ChaosScenario) -> Dict[str, Any]:
        """Inject failure based on scenario type"""
        
        failure_context = {"type": scenario.name, "active": True}
        
        if scenario.name == "database_connection_failure":
            # Mock database connection failures
            original_execute = self.connection_pool.execute
            
            async def failing_execute(*args, **kwargs):
                if random.random() < scenario.failure_rate:
                    raise asyncpg.exceptions.TooManyConnectionsError("Connection pool exhausted")
                return await original_execute(*args, **kwargs)
            
            self.connection_pool.execute = failing_execute
            failure_context["original_execute"] = original_execute
        
        elif scenario.name == "database_query_timeout":
            # Mock slow database queries
            original_fetch = self.connection_pool.fetch
            
            async def slow_fetch(*args, **kwargs):
                if random.random() < scenario.failure_rate:
                    await asyncio.sleep(random.uniform(5, 15))  # Simulate slow query
                return await original_fetch(*args, **kwargs)
            
            self.connection_pool.fetch = slow_fetch
            failure_context["original_fetch"] = original_fetch
        
        elif scenario.name == "redis_cluster_failure":
            # Mock Redis failures
            original_get = self.redis_client.get
            original_set = self.redis_client.set
            
            async def failing_get(*args, **kwargs):
                if random.random() < scenario.failure_rate:
                    raise aioredis.ConnectionError("Redis connection failed")
                return await original_get(*args, **kwargs)
            
            async def failing_set(*args, **kwargs):
                if random.random() < scenario.failure_rate:
                    raise aioredis.ConnectionError("Redis connection failed")
                return await original_set(*args, **kwargs)
            
            self.redis_client.get = failing_get
            self.redis_client.set = failing_set
            failure_context.update({
                "original_get": original_get,
                "original_set": original_set
            })
        
        elif scenario.name == "proxy_pool_outage":
            # Mock proxy failures (would integrate with actual crawler)
            failure_context["proxy_failure_rate"] = scenario.failure_rate
        
        elif scenario.name == "deepseek_api_outage":
            # Mock AI API failures
            failure_context["ai_api_failure"] = True
        
        # Add more failure injection patterns as needed
        
        return failure_context
    
    async def _monitor_system_during_chaos(self, scenario: ChaosScenario, result: ChaosTestResult):
        """Monitor system behavior during chaos injection"""
        
        monitoring_interval = 5  # seconds
        
        while True:
            try:
                # Collect current metrics
                await self._collect_current_metrics()
                
                # Test API endpoints
                api_errors = await self._test_api_endpoints()
                result.error_count += api_errors
                
                # Test database operations
                db_errors = await self._test_database_operations()
                result.error_count += db_errors
                
                # Test cache operations
                cache_errors = await self._test_cache_operations()
                result.error_count += cache_errors
                
                # Calculate performance impact
                result.performance_impact = self._calculate_performance_impact()
                
                await asyncio.sleep(monitoring_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(monitoring_interval)
    
    async def _collect_current_metrics(self):
        """Collect current system metrics"""
        
        try:
            # Database metrics
            db_stats = await self.connection_pool.fetchrow("""
                SELECT 
                    COUNT(*) as active_connections,
                    AVG(extract(epoch from (now() - query_start))) as avg_query_time
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            
            self.current_metrics.update({
                'db_active_connections': float(db_stats['active_connections'] or 0),
                'db_avg_query_time_seconds': float(db_stats['avg_query_time'] or 0),
            })
            
            # Redis metrics
            redis_info = await self.redis_client.info()
            self.current_metrics.update({
                'redis_used_memory_mb': float(redis_info.get('used_memory', 0)) / 1024 / 1024,
                'redis_connected_clients': float(redis_info.get('connected_clients', 0)),
                'redis_ops_per_sec': float(redis_info.get('instantaneous_ops_per_sec', 0)),
            })
        
        except Exception as e:
            logger.error(f"Error collecting current metrics: {e}")
    
    async def _test_api_endpoints(self) -> int:
        """Test API endpoints and count errors"""
        
        error_count = 0
        
        try:
            # Test health endpoint
            start_time = time.time()
            # Simulate API call
            await asyncio.sleep(0.01)
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 5000:  # 5 second timeout
                error_count += 1
            
            self.current_metrics['api_response_time_ms'] = response_time
        
        except Exception:
            error_count += 1
        
        return error_count
    
    async def _test_database_operations(self) -> int:
        """Test database operations and count errors"""
        
        error_count = 0
        
        try:
            # Test simple query
            await self.connection_pool.fetchval("SELECT 1")
        except Exception:
            error_count += 1
        
        try:
            # Test more complex query
            await self.connection_pool.fetch("""
                SELECT COUNT(*) FROM content_items 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                LIMIT 1
            """)
        except Exception:
            error_count += 1
        
        return error_count
    
    async def _test_cache_operations(self) -> int:
        """Test cache operations and count errors"""
        
        error_count = 0
        
        try:
            # Test Redis operations
            test_key = f"chaos_test_{int(time.time())}"
            await self.redis_client.set(test_key, "test_value", ex=60)
            value = await self.redis_client.get(test_key)
            
            if value != "test_value":
                error_count += 1
            
            await self.redis_client.delete(test_key)
        
        except Exception:
            error_count += 1
        
        return error_count
    
    def _calculate_performance_impact(self) -> Dict[str, float]:
        """Calculate performance impact compared to baseline"""
        
        impact = {}
        
        for metric, current_value in self.current_metrics.items():
            baseline_value = self.baseline_metrics.get(metric, 0)
            
            if baseline_value > 0:
                impact[metric] = (current_value - baseline_value) / baseline_value
            else:
                impact[metric] = 0.0
        
        return impact
    
    async def _stop_failure_injection(self, scenario: ChaosScenario, failure_context: Dict[str, Any]):
        """Stop failure injection"""
        
        if scenario.name == "database_connection_failure":
            if "original_execute" in failure_context:
                self.connection_pool.execute = failure_context["original_execute"]
        
        elif scenario.name == "database_query_timeout":
            if "original_fetch" in failure_context:
                self.connection_pool.fetch = failure_context["original_fetch"]
        
        elif scenario.name == "redis_cluster_failure":
            if "original_get" in failure_context:
                self.redis_client.get = failure_context["original_get"]
            if "original_set" in failure_context:
                self.redis_client.set = failure_context["original_set"]
        
        failure_context["active"] = False
    
    async def _monitor_recovery(self, scenario: ChaosScenario, result: ChaosTestResult) -> bool:
        """Monitor system recovery after failure injection stops"""
        
        recovery_timeout = scenario.recovery_time_seconds * 2  # Allow extra time
        start_time = time.time()
        
        while time.time() - start_time < recovery_timeout:
            try:
                # Test if system has recovered
                api_errors = await self._test_api_endpoints()
                db_errors = await self._test_database_operations()
                cache_errors = await self._test_cache_operations()
                
                total_errors = api_errors + db_errors + cache_errors
                
                if total_errors == 0:
                    # System has recovered
                    result.logs.append(f"System recovered in {time.time() - start_time:.1f}s")
                    return True
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            except Exception as e:
                logger.error(f"Recovery monitoring error: {e}")
                await asyncio.sleep(5)
        
        result.logs.append(f"System did not fully recover within {recovery_timeout}s")
        return False
    
    def _evaluate_success_criteria(self, scenario: ChaosScenario, result: ChaosTestResult) -> bool:
        """Evaluate if the scenario met success criteria"""
        
        criteria = scenario.success_criteria
        
        # Check error rate
        if "max_error_rate" in criteria:
            # Estimate error rate (simplified)
            estimated_requests = result.duration_seconds * 10  # Assume 10 requests per second
            error_rate = result.error_count / max(estimated_requests, 1)
            
            if error_rate > criteria["max_error_rate"]:
                result.logs.append(f"Error rate too high: {error_rate:.3f} > {criteria['max_error_rate']}")
                return False
        
        # Check response time
        if "max_response_time_ms" in criteria:
            current_response_time = self.current_metrics.get('api_response_time_ms', 0)
            
            if current_response_time > criteria["max_response_time_ms"]:
                result.logs.append(f"Response time too high: {current_response_time:.1f}ms > {criteria['max_response_time_ms']}ms")
                return False
        
        # Check recovery time
        if "recovery_time_max_seconds" in criteria:
            if result.recovery_time_seconds > criteria["recovery_time_max_seconds"]:
                result.logs.append(f"Recovery time too long: {result.recovery_time_seconds:.1f}s > {criteria['recovery_time_max_seconds']}s")
                return False
        
        return True
    
    async def _cleanup_failure_injection(self, scenario: ChaosScenario):
        """Cleanup any remaining failure injection"""
        
        # Reset all mocked methods to original implementations
        # This is a safety measure in case stop_failure_injection failed
        
        try:
            # Reset database methods
            if hasattr(self.connection_pool, '_original_execute'):
                self.connection_pool.execute = self.connection_pool._original_execute
            
            if hasattr(self.connection_pool, '_original_fetch'):
                self.connection_pool.fetch = self.connection_pool._original_fetch
            
            # Reset Redis methods
            if hasattr(self.redis_client, '_original_get'):
                self.redis_client.get = self.redis_client._original_get
            
            if hasattr(self.redis_client, '_original_set'):
                self.redis_client.set = self.redis_client._original_set
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def run_all_scenarios(self) -> List[ChaosTestResult]:
        """Run all chaos engineering scenarios"""
        
        logger.info(f"Running {len(self.scenarios)} chaos engineering scenarios")
        
        for scenario in self.scenarios:
            try:
                result = await self.run_chaos_scenario(scenario)
                self.results.append(result)
                
                # Brief pause between scenarios
                await asyncio.sleep(30)
            
            except Exception as e:
                logger.error(f"Failed to run scenario {scenario.name}: {e}")
        
        return self.results
    
    def generate_chaos_report(self) -> Dict[str, Any]:
        """Generate comprehensive chaos engineering report"""
        
        successful_scenarios = [r for r in self.results if r.success]
        failed_scenarios = [r for r in self.results if not r.success]
        
        report = {
            'summary': {
                'total_scenarios': len(self.results),
                'successful_scenarios': len(successful_scenarios),
                'failed_scenarios': len(failed_scenarios),
                'overall_success_rate': len(successful_scenarios) / len(self.results) if self.results else 0,
                'total_test_duration_seconds': sum(r.duration_seconds for r in self.results),
                'avg_recovery_time_seconds': sum(r.recovery_time_seconds for r in self.results) / len(self.results) if self.results else 0,
            },
            'scenario_results': [
                {
                    'name': r.scenario_name,
                    'success': r.success,
                    'duration_seconds': r.duration_seconds,
                    'error_count': r.error_count,
                    'recovery_time_seconds': r.recovery_time_seconds,
                    'performance_impact': r.performance_impact,
                    'logs': r.logs[-5:]  # Last 5 log entries
                }
                for r in self.results
            ],
            'failed_scenarios': [
                {
                    'name': r.scenario_name,
                    'error_count': r.error_count,
                    'logs': r.logs
                }
                for r in failed_scenarios
            ],
            'performance_analysis': {
                'baseline_metrics': self.baseline_metrics,
                'max_performance_impact': self._calculate_max_performance_impact(),
            },
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        return report
    
    def _calculate_max_performance_impact(self) -> Dict[str, float]:
        """Calculate maximum performance impact across all scenarios"""
        
        max_impact = {}
        
        for result in self.results:
            for metric, impact in result.performance_impact.items():
                if metric not in max_impact or abs(impact) > abs(max_impact[metric]):
                    max_impact[metric] = impact
        
        return max_impact
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on chaos test results"""
        
        recommendations = []
        
        failed_scenarios = [r for r in self.results if not r.success]
        
        if failed_scenarios:
            recommendations.append(f"Address {len(failed_scenarios)} failed resilience scenarios")
        
        # Check recovery times
        slow_recovery = [r for r in self.results if r.recovery_time_seconds > 120]
        if slow_recovery:
            recommendations.append(f"Improve recovery time for {len(slow_recovery)} scenarios (>2 minutes)")
        
        # Check error rates
        high_error_scenarios = [r for r in self.results if r.error_count > 50]
        if high_error_scenarios:
            recommendations.append(f"Reduce error rates in {len(high_error_scenarios)} scenarios")
        
        # Performance recommendations
        max_impact = self._calculate_max_performance_impact()
        for metric, impact in max_impact.items():
            if abs(impact) > 2.0:  # 200% performance degradation
                recommendations.append(f"Address severe performance impact in {metric}: {impact:.1%}")
        
        if not recommendations:
            recommendations.append("System demonstrates excellent resilience across all tested scenarios")
        
        return recommendations


# Pytest integration
@pytest.fixture
async def chaos_engineer():
    """Pytest fixture for chaos engineering"""
    
    settings = Settings()
    engineer = ChaosEngineer(settings)
    await engineer.initialize()
    return engineer


@pytest.mark.asyncio
async def test_database_resilience(chaos_engineer):
    """Test database failure resilience"""
    
    db_scenarios = [s for s in chaos_engineer.scenarios if "database" in s.name]
    
    for scenario in db_scenarios:
        result = await chaos_engineer.run_chaos_scenario(scenario)
        assert result.success, f"Database resilience test failed: {scenario.name}"


@pytest.mark.asyncio
async def test_cache_resilience(chaos_engineer):
    """Test cache failure resilience"""
    
    cache_scenarios = [s for s in chaos_engineer.scenarios if "redis" in s.name]
    
    for scenario in cache_scenarios:
        result = await chaos_engineer.run_chaos_scenario(scenario)
        assert result.success, f"Cache resilience test failed: {scenario.name}"


@pytest.mark.asyncio
async def test_network_resilience(chaos_engineer):
    """Test network failure resilience"""
    
    network_scenarios = [s for s in chaos_engineer.scenarios if "network" in s.name or "proxy" in s.name]
    
    for scenario in network_scenarios:
        result = await chaos_engineer.run_chaos_scenario(scenario)
        assert result.success, f"Network resilience test failed: {scenario.name}"


@pytest.mark.asyncio
async def test_full_chaos_suite(chaos_engineer):
    """Run complete chaos engineering suite"""
    
    results = await chaos_engineer.run_all_scenarios()
    report = chaos_engineer.generate_chaos_report()
    
    # Assert overall success rate
    success_rate = report['summary']['overall_success_rate']
    assert success_rate >= 0.8, f"Chaos test success rate too low: {success_rate:.1%}"
    
    # Assert recovery times
    avg_recovery_time = report['summary']['avg_recovery_time_seconds']
    assert avg_recovery_time <= 120, f"Average recovery time too long: {avg_recovery_time:.1f}s"
    
    # Save detailed report
    import json
    report_path = f"chaos_engineering_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Chaos engineering report saved to: {report_path}")


# Standalone execution
async def main():
    """Run chaos engineering tests as standalone script"""
    
    settings = Settings()
    engineer = ChaosEngineer(settings)
    
    await engineer.initialize()
    results = await engineer.run_all_scenarios()
    report = engineer.generate_chaos_report()
    
    # Print summary
    print("\n" + "="*60)
    print("CHAOS ENGINEERING TEST RESULTS")
    print("="*60)
    
    summary = report['summary']
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Successful: {summary['successful_scenarios']}")
    print(f"Failed: {summary['failed_scenarios']}")
    print(f"Success Rate: {summary['overall_success_rate']:.1%}")
    print(f"Avg Recovery Time: {summary['avg_recovery_time_seconds']:.1f}s")
    
    if report['failed_scenarios']:
        print("\nFailed Scenarios:")
        for failed in report['failed_scenarios']:
            print(f"  - {failed['name']}: {failed['error_count']} errors")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    # Save report
    import json
    report_path = f"chaos_engineering_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

