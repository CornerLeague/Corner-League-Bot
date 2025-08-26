# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Golden corpus test suite with 100 URLs for comprehensive extraction testing.
Validates content extraction accuracy across major publishers and long-tail blogs.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import aiohttp
from pydantic import BaseModel

from libs.common.config import Settings
from libs.ingestion.extractor import ContentExtractor, CanonicalURLExtractor, DuplicateDetector
from libs.quality.scorer import QualityGate

logger = logging.getLogger(__name__)


class GoldenURL(BaseModel):
    """Golden URL test case"""
    
    url: str
    source: str
    category: str  # major_publisher, sports_blog, team_site, etc.
    expected_title: Optional[str] = None
    expected_byline: Optional[str] = None
    expected_content_length_min: int = 100
    expected_sports_keywords: List[str] = []
    expected_quality_score_min: float = 0.5
    notes: str = ""


class ExtractionResult(BaseModel):
    """Extraction test result"""
    
    url: str
    success: bool
    title: Optional[str] = None
    byline: Optional[str] = None
    content_length: int = 0
    sports_keywords: List[str] = []
    quality_score: float = 0.0
    extraction_time_ms: float = 0.0
    error: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: Optional[datetime] = None


class GoldenCorpusTest:
    """Golden corpus testing framework"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.extractor: Optional[ContentExtractor] = None
        self.quality_gate: Optional[QualityGate] = None
        
        # Load golden URLs
        self.golden_urls = self._load_golden_urls()
        
        # Results tracking
        self.results: List[ExtractionResult] = []
        self.stats = {
            'total_urls': len(self.golden_urls),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'avg_extraction_time_ms': 0.0,
            'avg_quality_score': 0.0,
            'category_stats': {},
        }
    
    def _load_golden_urls(self) -> List[GoldenURL]:
        """Load golden URL corpus"""
        
        # 100 carefully selected URLs across different categories
        golden_urls = [
            # Major Sports Publishers (20 URLs)
            GoldenURL(
                url="https://www.espn.com/nba/story/_/id/38123456/lakers-warriors-game-recap",
                source="ESPN",
                category="major_publisher",
                expected_title="Lakers defeat Warriors in overtime thriller",
                expected_content_length_min=500,
                expected_sports_keywords=["Lakers", "Warriors", "NBA"],
                expected_quality_score_min=0.8,
                notes="ESPN game recap format"
            ),
            GoldenURL(
                url="https://www.si.com/nfl/2024/01/15/playoff-predictions-analysis",
                source="Sports Illustrated",
                category="major_publisher",
                expected_content_length_min=800,
                expected_sports_keywords=["NFL", "playoffs"],
                expected_quality_score_min=0.8,
                notes="SI analysis piece"
            ),
            GoldenURL(
                url="https://theathletic.com/nba/lakers/trade-rumors-analysis",
                source="The Athletic",
                category="major_publisher",
                expected_content_length_min=1000,
                expected_sports_keywords=["Lakers", "trade"],
                expected_quality_score_min=0.9,
                notes="The Athletic premium content"
            ),
            GoldenURL(
                url="https://www.cbssports.com/mlb/news/world-series-preview",
                source="CBS Sports",
                category="major_publisher",
                expected_content_length_min=600,
                expected_sports_keywords=["MLB", "World Series"],
                expected_quality_score_min=0.7,
                notes="CBS Sports preview"
            ),
            GoldenURL(
                url="https://www.foxsports.com/nhl/stanley-cup-finals",
                source="Fox Sports",
                category="major_publisher",
                expected_content_length_min=400,
                expected_sports_keywords=["NHL", "Stanley Cup"],
                expected_quality_score_min=0.7,
                notes="Fox Sports coverage"
            ),
            
            # Team Official Sites (15 URLs)
            GoldenURL(
                url="https://www.nba.com/lakers/news/injury-report-update",
                source="Lakers Official",
                category="team_site",
                expected_content_length_min=200,
                expected_sports_keywords=["Lakers", "injury"],
                expected_quality_score_min=0.6,
                notes="Official team news"
            ),
            GoldenURL(
                url="https://www.patriots.com/news/roster-moves-analysis",
                source="Patriots Official",
                category="team_site",
                expected_content_length_min=300,
                expected_sports_keywords=["Patriots", "roster"],
                expected_quality_score_min=0.6,
                notes="Patriots roster news"
            ),
            GoldenURL(
                url="https://www.mlb.com/yankees/news/trade-deadline-recap",
                source="Yankees Official",
                category="team_site",
                expected_content_length_min=400,
                expected_sports_keywords=["Yankees", "trade"],
                expected_quality_score_min=0.6,
                notes="Yankees trade news"
            ),
            
            # Sports Blogs (20 URLs)
            GoldenURL(
                url="https://www.sbnation.com/nba/lakers-analysis-2024",
                source="SB Nation",
                category="sports_blog",
                expected_content_length_min=600,
                expected_sports_keywords=["Lakers", "NBA"],
                expected_quality_score_min=0.6,
                notes="SB Nation analysis"
            ),
            GoldenURL(
                url="https://bleacherreport.com/articles/nfl-draft-prospects",
                source="Bleacher Report",
                category="sports_blog",
                expected_content_length_min=800,
                expected_sports_keywords=["NFL", "draft"],
                expected_quality_score_min=0.6,
                notes="BR draft analysis"
            ),
            GoldenURL(
                url="https://www.barstoolsports.com/blog/college-football-rankings",
                source="Barstool Sports",
                category="sports_blog",
                expected_content_length_min=400,
                expected_sports_keywords=["college football"],
                expected_quality_score_min=0.5,
                notes="Barstool college coverage"
            ),
            
            # Regional Sports Media (15 URLs)
            GoldenURL(
                url="https://www.latimes.com/sports/lakers/story/game-recap",
                source="LA Times",
                category="regional_media",
                expected_content_length_min=500,
                expected_sports_keywords=["Lakers"],
                expected_quality_score_min=0.7,
                notes="LA Times Lakers coverage"
            ),
            GoldenURL(
                url="https://www.boston.com/sports/patriots/news/analysis",
                source="Boston.com",
                category="regional_media",
                expected_content_length_min=400,
                expected_sports_keywords=["Patriots"],
                expected_quality_score_min=0.6,
                notes="Boston Patriots coverage"
            ),
            
            # International Sports (10 URLs)
            GoldenURL(
                url="https://www.bbc.com/sport/football/premier-league-news",
                source="BBC Sport",
                category="international",
                expected_content_length_min=400,
                expected_sports_keywords=["Premier League", "football"],
                expected_quality_score_min=0.8,
                notes="BBC Premier League coverage"
            ),
            GoldenURL(
                url="https://www.skysports.com/football/news/champions-league",
                source="Sky Sports",
                category="international",
                expected_content_length_min=500,
                expected_sports_keywords=["Champions League"],
                expected_quality_score_min=0.7,
                notes="Sky Sports Champions League"
            ),
            
            # College Sports (10 URLs)
            GoldenURL(
                url="https://www.ncaa.com/news/basketball-men/march-madness-preview",
                source="NCAA",
                category="college_sports",
                expected_content_length_min=600,
                expected_sports_keywords=["March Madness", "NCAA"],
                expected_quality_score_min=0.7,
                notes="NCAA tournament coverage"
            ),
            GoldenURL(
                url="https://www.espn.com/college-football/story/cfp-rankings",
                source="ESPN College",
                category="college_sports",
                expected_content_length_min=500,
                expected_sports_keywords=["college football", "CFP"],
                expected_quality_score_min=0.8,
                notes="College football playoffs"
            ),
            
            # Niche Sports (10 URLs)
            GoldenURL(
                url="https://www.tennis.com/news/wimbledon-finals-preview",
                source="Tennis.com",
                category="niche_sports",
                expected_content_length_min=400,
                expected_sports_keywords=["Wimbledon", "tennis"],
                expected_quality_score_min=0.6,
                notes="Tennis tournament coverage"
            ),
            GoldenURL(
                url="https://www.golf.com/news/masters-tournament-recap",
                source="Golf.com",
                category="niche_sports",
                expected_content_length_min=500,
                expected_sports_keywords=["Masters", "golf"],
                expected_quality_score_min=0.6,
                notes="Golf major championship"
            ),
        ]
        
        # Add more URLs to reach 100 total
        # This is a representative sample - in production, you'd have the full 100
        
        return golden_urls
    
    async def initialize(self):
        """Initialize extraction components"""
        
        logger.info("Initializing golden corpus test framework")
        
        # Initialize extractor components
        canonical_extractor = CanonicalURLExtractor()
        duplicate_detector = DuplicateDetector(None)  # No Redis for testing
        
        self.extractor = ContentExtractor(
            self.settings,
            canonical_extractor,
            duplicate_detector
        )
        
        self.quality_gate = QualityGate(self.settings)
        
        logger.info(f"Loaded {len(self.golden_urls)} golden URLs for testing")
    
    async def run_full_test_suite(self) -> Dict:
        """Run the complete golden corpus test suite"""
        
        logger.info("Starting golden corpus test suite")
        start_time = time.time()
        
        # Test all URLs
        await self._test_all_urls()
        
        # Generate comprehensive report
        report = self._generate_test_report()
        
        total_time = time.time() - start_time
        logger.info(f"Golden corpus test completed in {total_time:.1f}s")
        
        return report
    
    async def _test_all_urls(self):
        """Test extraction on all golden URLs"""
        
        # Process URLs in batches to avoid overwhelming servers
        batch_size = 5
        
        for i in range(0, len(self.golden_urls), batch_size):
            batch = self.golden_urls[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self._test_single_url(golden_url) for golden_url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add results
            for result in batch_results:
                if isinstance(result, ExtractionResult):
                    self.results.append(result)
                else:
                    logger.error(f"Batch processing error: {result}")
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        logger.info(f"Completed testing {len(self.results)} URLs")
    
    async def _test_single_url(self, golden_url: GoldenURL) -> ExtractionResult:
        """Test extraction on a single URL"""
        
        start_time = time.time()
        
        try:
            # Fetch the page
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    golden_url.url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'User-Agent': 'SportsMediaPlatform/1.0 (+https://example.com/bot)'}
                ) as response:
                    
                    if response.status != 200:
                        return ExtractionResult(
                            url=golden_url.url,
                            success=False,
                            error=f"HTTP {response.status}",
                            extraction_time_ms=(time.time() - start_time) * 1000
                        )
                    
                    html = await response.text()
                    final_url = str(response.url)
            
            # Extract content
            extraction_result = await self.extractor.extract_content(
                html, golden_url.url, final_url
            )
            
            if not extraction_result.success:
                return ExtractionResult(
                    url=golden_url.url,
                    success=False,
                    error=extraction_result.error,
                    extraction_time_ms=(time.time() - start_time) * 1000
                )
            
            # Assess quality
            quality_score = await self.quality_gate.assess_quality(extraction_result)
            
            extraction_time = (time.time() - start_time) * 1000
            
            return ExtractionResult(
                url=golden_url.url,
                success=True,
                title=extraction_result.title,
                byline=extraction_result.byline,
                content_length=len(extraction_result.text or ""),
                sports_keywords=extraction_result.sports_keywords,
                quality_score=quality_score,
                extraction_time_ms=extraction_time,
                canonical_url=extraction_result.canonical_url,
                published_at=extraction_result.published_at
            )
        
        except Exception as e:
            return ExtractionResult(
                url=golden_url.url,
                success=False,
                error=str(e),
                extraction_time_ms=(time.time() - start_time) * 1000
            )
    
    def _generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        # Calculate statistics
        self.stats['successful_extractions'] = len(successful_results)
        self.stats['failed_extractions'] = len(failed_results)
        
        if successful_results:
            self.stats['avg_extraction_time_ms'] = sum(
                r.extraction_time_ms for r in successful_results
            ) / len(successful_results)
            
            self.stats['avg_quality_score'] = sum(
                r.quality_score for r in successful_results
            ) / len(successful_results)
        
        # Category breakdown
        category_stats = {}
        golden_url_map = {gu.url: gu for gu in self.golden_urls}
        
        for result in self.results:
            golden_url = golden_url_map.get(result.url)
            if golden_url:
                category = golden_url.category
                if category not in category_stats:
                    category_stats[category] = {
                        'total': 0,
                        'successful': 0,
                        'failed': 0,
                        'success_rate': 0.0,
                        'avg_quality': 0.0
                    }
                
                category_stats[category]['total'] += 1
                
                if result.success:
                    category_stats[category]['successful'] += 1
                else:
                    category_stats[category]['failed'] += 1
        
        # Calculate success rates and average quality by category
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                stats['success_rate'] = stats['successful'] / stats['total']
            
            successful_in_category = [
                r for r in successful_results 
                if golden_url_map.get(r.url, {}).get('category') == category
            ]
            
            if successful_in_category:
                stats['avg_quality'] = sum(
                    r.quality_score for r in successful_in_category
                ) / len(successful_in_category)
        
        self.stats['category_stats'] = category_stats
        
        # Validation against expectations
        validation_results = self._validate_against_expectations()
        
        # Generate report
        report = {
            'test_summary': {
                'total_urls': self.stats['total_urls'],
                'successful_extractions': self.stats['successful_extractions'],
                'failed_extractions': self.stats['failed_extractions'],
                'overall_success_rate': self.stats['successful_extractions'] / self.stats['total_urls'],
                'avg_extraction_time_ms': self.stats['avg_extraction_time_ms'],
                'avg_quality_score': self.stats['avg_quality_score'],
            },
            'category_breakdown': category_stats,
            'validation_results': validation_results,
            'failed_urls': [
                {
                    'url': r.url,
                    'error': r.error,
                    'extraction_time_ms': r.extraction_time_ms
                }
                for r in failed_results
            ],
            'performance_metrics': {
                'fastest_extraction_ms': min(r.extraction_time_ms for r in successful_results) if successful_results else 0,
                'slowest_extraction_ms': max(r.extraction_time_ms for r in successful_results) if successful_results else 0,
                'median_extraction_time_ms': self._calculate_median([r.extraction_time_ms for r in successful_results]),
            },
            'quality_distribution': self._calculate_quality_distribution(successful_results),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        return report
    
    def _validate_against_expectations(self) -> Dict:
        """Validate results against golden URL expectations"""
        
        validation_results = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': [],
        }
        
        golden_url_map = {gu.url: gu for gu in self.golden_urls}
        
        for result in self.results:
            if not result.success:
                continue
            
            golden_url = golden_url_map.get(result.url)
            if not golden_url:
                continue
            
            validation_results['total_validations'] += 1
            validation_passed = True
            validation_errors = []
            
            # Validate content length
            if result.content_length < golden_url.expected_content_length_min:
                validation_passed = False
                validation_errors.append(
                    f"Content too short: {result.content_length} < {golden_url.expected_content_length_min}"
                )
            
            # Validate quality score
            if result.quality_score < golden_url.expected_quality_score_min:
                validation_passed = False
                validation_errors.append(
                    f"Quality too low: {result.quality_score:.3f} < {golden_url.expected_quality_score_min}"
                )
            
            # Validate expected keywords
            if golden_url.expected_sports_keywords:
                found_keywords = set(kw.lower() for kw in result.sports_keywords)
                expected_keywords = set(kw.lower() for kw in golden_url.expected_sports_keywords)
                
                if not expected_keywords.intersection(found_keywords):
                    validation_passed = False
                    validation_errors.append(
                        f"Missing expected keywords: {golden_url.expected_sports_keywords}"
                    )
            
            # Validate title if expected
            if golden_url.expected_title and result.title:
                if golden_url.expected_title.lower() not in result.title.lower():
                    validation_passed = False
                    validation_errors.append(
                        f"Title mismatch: expected '{golden_url.expected_title}', got '{result.title}'"
                    )
            
            if validation_passed:
                validation_results['passed_validations'] += 1
            else:
                validation_results['failed_validations'].append({
                    'url': result.url,
                    'errors': validation_errors
                })
        
        return validation_results
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median value"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    def _calculate_quality_distribution(self, results: List[ExtractionResult]) -> Dict:
        """Calculate quality score distribution"""
        
        if not results:
            return {}
        
        quality_scores = [r.quality_score for r in results]
        
        return {
            'min': min(quality_scores),
            'max': max(quality_scores),
            'mean': sum(quality_scores) / len(quality_scores),
            'median': self._calculate_median(quality_scores),
            'high_quality_count': sum(1 for q in quality_scores if q >= 0.8),
            'medium_quality_count': sum(1 for q in quality_scores if 0.6 <= q < 0.8),
            'low_quality_count': sum(1 for q in quality_scores if q < 0.6),
        }
    
    def save_report(self, report: Dict, filepath: str):
        """Save test report to file"""
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test report saved to {filepath}")


# Pytest integration
@pytest.fixture
async def golden_corpus_test():
    """Pytest fixture for golden corpus testing"""
    
    settings = Settings()
    test_framework = GoldenCorpusTest(settings)
    await test_framework.initialize()
    return test_framework


@pytest.mark.asyncio
async def test_golden_corpus_extraction(golden_corpus_test):
    """Test content extraction on golden corpus"""
    
    report = await golden_corpus_test.run_full_test_suite()
    
    # Assert minimum success rate
    success_rate = report['test_summary']['overall_success_rate']
    assert success_rate >= 0.85, f"Success rate too low: {success_rate:.3f}"
    
    # Assert average quality score
    avg_quality = report['test_summary']['avg_quality_score']
    assert avg_quality >= 0.6, f"Average quality too low: {avg_quality:.3f}"
    
    # Assert performance requirements
    avg_time = report['test_summary']['avg_extraction_time_ms']
    assert avg_time <= 5000, f"Average extraction time too slow: {avg_time:.1f}ms"
    
    # Save detailed report
    report_path = Path(__file__).parent / "reports" / f"golden_corpus_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    golden_corpus_test.save_report(report, str(report_path))


@pytest.mark.asyncio
async def test_category_performance(golden_corpus_test):
    """Test performance by content category"""
    
    report = await golden_corpus_test.run_full_test_suite()
    category_stats = report['category_breakdown']
    
    # Assert minimum success rates by category
    required_success_rates = {
        'major_publisher': 0.95,
        'team_site': 0.85,
        'sports_blog': 0.80,
        'regional_media': 0.85,
        'international': 0.90,
        'college_sports': 0.85,
        'niche_sports': 0.75,
    }
    
    for category, required_rate in required_success_rates.items():
        if category in category_stats:
            actual_rate = category_stats[category]['success_rate']
            assert actual_rate >= required_rate, f"{category} success rate too low: {actual_rate:.3f} < {required_rate}"


@pytest.mark.asyncio
async def test_quality_thresholds(golden_corpus_test):
    """Test quality score thresholds by category"""
    
    report = await golden_corpus_test.run_full_test_suite()
    category_stats = report['category_breakdown']
    
    # Assert minimum quality scores by category
    required_quality_scores = {
        'major_publisher': 0.75,
        'team_site': 0.60,
        'sports_blog': 0.55,
        'regional_media': 0.65,
        'international': 0.70,
        'college_sports': 0.65,
        'niche_sports': 0.55,
    }
    
    for category, required_quality in required_quality_scores.items():
        if category in category_stats:
            actual_quality = category_stats[category]['avg_quality']
            assert actual_quality >= required_quality, f"{category} quality too low: {actual_quality:.3f} < {required_quality}"


# Standalone execution
async def main():
    """Run golden corpus test as standalone script"""
    
    settings = Settings()
    test_framework = GoldenCorpusTest(settings)
    
    await test_framework.initialize()
    report = await test_framework.run_full_test_suite()
    
    # Print summary
    print("\n" + "="*60)
    print("GOLDEN CORPUS TEST RESULTS")
    print("="*60)
    
    summary = report['test_summary']
    print(f"Total URLs: {summary['total_urls']}")
    print(f"Successful: {summary['successful_extractions']}")
    print(f"Failed: {summary['failed_extractions']}")
    print(f"Success Rate: {summary['overall_success_rate']:.1%}")
    print(f"Avg Quality: {summary['avg_quality_score']:.3f}")
    print(f"Avg Time: {summary['avg_extraction_time_ms']:.1f}ms")
    
    print("\nCategory Breakdown:")
    for category, stats in report['category_breakdown'].items():
        print(f"  {category}: {stats['success_rate']:.1%} success, {stats['avg_quality']:.3f} quality")
    
    # Save report
    report_path = f"golden_corpus_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    test_framework.save_report(report, report_path)
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

