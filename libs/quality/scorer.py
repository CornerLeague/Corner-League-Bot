# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Content quality scoring system with multi-signal analysis.
Implements shadow mode for safe deployment and source reputation feedback.
"""

import logging
import math
import re
from datetime import datetime, timedelta
from typing import Any

from libs.common.config import Settings, get_settings

logger = logging.getLogger(__name__)


class QualitySignal:
    """Individual quality signal with weight and computation"""

    def __init__(self, name: str, weight: float = 1.0, description: str = ""):
        self.name = name
        self.weight = weight
        self.description = description

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute signal value (0.0 to 1.0)"""
        raise NotImplementedError

    def __repr__(self):
        return f"QualitySignal(name='{self.name}', weight={self.weight})"


class SourceReputationSignal(QualitySignal):
    """Source reputation based on historical performance"""

    def __init__(self):
        super().__init__(
            name="source_reputation",
            weight=0.25,
            description="Source reputation based on historical quality and reliability"
        )

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute source reputation score"""

        reputation_score = source.get("reputation_score", 0.5)
        quality_tier = source.get("quality_tier", 2)
        success_rate = source.get("success_rate", 1.0)

        # Tier-based scoring
        tier_scores = {1: 0.9, 2: 0.7, 3: 0.5}  # premium, quality, discovery
        tier_score = tier_scores.get(quality_tier, 0.5)

        # Combine reputation, tier, and success rate
        score = (reputation_score * 0.6 + tier_score * 0.3 + success_rate * 0.1)

        return max(0.0, min(1.0, score))


class FreshnessSignal(QualitySignal):
    """Content freshness based on publication date"""

    def __init__(self):
        super().__init__(
            name="freshness",
            weight=0.15,
            description="Content freshness with exponential decay"
        )

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute freshness score with exponential decay"""

        published_at = content.get("published_at")
        if not published_at:
            return 0.3  # Default for unknown publication date

        if isinstance(published_at, str):
            try:
                from dateutil.parser import parse
                published_at = parse(published_at)
            except:
                return 0.3

        # Calculate age in hours
        now = datetime.utcnow()
        if published_at.tzinfo:
            published_at = published_at.replace(tzinfo=None)

        age_hours = (now - published_at).total_seconds() / 3600

        # Exponential decay: score = e^(-age/half_life)
        half_life_hours = 24  # 50% score after 24 hours
        score = math.exp(-age_hours / half_life_hours)

        return max(0.0, min(1.0, score))


class ContentDepthSignal(QualitySignal):
    """Content depth based on word count and structure"""

    def __init__(self):
        super().__init__(
            name="content_depth",
            weight=0.20,
            description="Content depth based on length, structure, and information density"
        )

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute content depth score"""

        word_count = content.get("word_count", 0)
        text = content.get("text", "")
        title = content.get("title", "")

        # Word count scoring (optimal range: 300-2000 words)
        if word_count < 100:
            length_score = 0.1
        elif word_count < 300:
            length_score = word_count / 300 * 0.6
        elif word_count <= 2000:
            length_score = 0.6 + (word_count - 300) / 1700 * 0.4
        else:
            # Diminishing returns for very long content
            length_score = 1.0 - min(0.3, (word_count - 2000) / 5000)

        # Structure scoring
        structure_score = self._analyze_structure(text, title)

        # Information density (unique words / total words)
        density_score = self._calculate_density(text)

        # Combine scores
        score = (length_score * 0.5 + structure_score * 0.3 + density_score * 0.2)

        return max(0.0, min(1.0, score))

    def _analyze_structure(self, text: str, title: str) -> float:
        """Analyze content structure quality"""

        if not text:
            return 0.0

        score = 0.0

        # Check for proper sentences
        sentences = re.split(r"[.!?]+", text)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if len(valid_sentences) >= 3:
            score += 0.3

        # Check for paragraphs (assuming double newlines)
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
        if len(paragraphs) >= 2:
            score += 0.3

        # Check title quality
        if title and len(title.split()) >= 4:
            score += 0.2

        # Check for quotes (indicates reporting)
        if '"' in text or '"' in text or '"' in text:
            score += 0.2

        return min(1.0, score)

    def _calculate_density(self, text: str) -> float:
        """Calculate information density"""

        if not text:
            return 0.0

        words = text.lower().split()
        if len(words) < 10:
            return 0.0

        unique_words = set(words)
        density = len(unique_words) / len(words)

        # Normalize to 0-1 range (typical density is 0.4-0.8)
        normalized_density = max(0.0, min(1.0, (density - 0.2) / 0.6))

        return normalized_density


class TitleQualitySignal(QualitySignal):
    """Title quality based on heuristics"""

    def __init__(self):
        super().__init__(
            name="title_quality",
            weight=0.15,
            description="Title quality based on length, clickbait detection, and clarity"
        )

        # Clickbait patterns
        self.clickbait_patterns = [
            r"\b(you won\'t believe|shocking|amazing|incredible)\b",
            r"\b(this will|you need to|must see|will blow your mind)\b",
            r"\b(number \d+ will|reason \d+ is|things? you)\b",
            r"\b(hate him|doctors hate|one weird trick)\b",
            r"^(\d+\s+(ways?|things?|reasons?|secrets?))",
            r"\b(gone wrong|gone right|what happens next)\b",
        ]

        self.clickbait_regex = re.compile("|".join(self.clickbait_patterns), re.IGNORECASE)

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute title quality score"""

        title = content.get("title", "")
        if not title:
            return 0.0

        score = 1.0

        # Length scoring (optimal: 40-80 characters)
        title_length = len(title)
        if title_length < 20:
            score *= 0.5
        elif title_length < 40:
            score *= 0.7 + (title_length - 20) / 20 * 0.3
        elif title_length <= 80:
            pass  # Optimal range
        else:
            score *= max(0.6, 1.0 - (title_length - 80) / 100)

        # Clickbait detection
        if self.clickbait_regex.search(title):
            score *= 0.3

        # All caps penalty
        if title.isupper() and len(title) > 10:
            score *= 0.4

        # Excessive punctuation penalty
        punct_count = sum(1 for c in title if c in "!?")
        if punct_count > 2:
            score *= 0.6

        # Word quality
        words = title.split()
        if len(words) < 3:
            score *= 0.5

        # Check for proper capitalization
        if title.istitle() or (title[0].isupper() and not title[1:].isupper()):
            score *= 1.1  # Bonus for proper capitalization

        return max(0.0, min(1.0, score))


class SportsRelevanceSignal(QualitySignal):
    """Sports content relevance scoring"""

    def __init__(self):
        super().__init__(
            name="sports_relevance",
            weight=0.15,
            description="Relevance to sports content based on keywords and entities"
        )

        # Sports entity patterns
        self.sports_patterns = {
            "high_value": [
                r"\b(NBA|NFL|MLB|NHL|MLS|NCAA)\b",
                r"\b(Lakers|Warriors|Patriots|Cowboys|Yankees|Dodgers)\b",
                r"\b(LeBron|Brady|Mahomes|Curry|Judge|Ohtani)\b",
                r"\b(Super Bowl|World Series|NBA Finals|Stanley Cup)\b",
                r"\b(playoffs?|championship|finals?|draft)\b",
            ],
            "medium_value": [
                r"\b(basketball|football|baseball|hockey|soccer|tennis|golf)\b",
                r"\b(game|match|season|player|team|coach|trade)\b",
                r"\b(score|points?|goals?|runs?|yards?|stats?)\b",
                r"\b(injury|injured|contract|signing|free agent)\b",
            ],
            "low_value": [
                r"\b(sport|sports|athletic|competition|tournament)\b",
                r"\b(win|wins|won|lose|lost|victory|defeat)\b",
                r"\b(training|practice|workout|fitness)\b",
            ]
        }

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute sports relevance score"""

        title = content.get("title", "")
        text = content.get("text", "")
        sports_keywords = content.get("sports_keywords", [])

        combined_text = f"{title} {text}".lower()

        score = 0.0

        # Keyword-based scoring
        if sports_keywords:
            score += min(0.4, len(sports_keywords) * 0.1)

        # Pattern-based scoring
        for value_tier, patterns in self.sports_patterns.items():
            tier_score = 0.0

            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                if matches > 0:
                    if value_tier == "high_value":
                        tier_score += matches * 0.2
                    elif value_tier == "medium_value":
                        tier_score += matches * 0.1
                    else:  # low_value
                        tier_score += matches * 0.05

            score += min(0.3, tier_score)

        # Content type bonus
        content_type = content.get("content_type")
        if content_type in ["game_recap", "breaking_news", "trade", "injury"]:
            score += 0.2
        elif content_type in ["analysis", "interview"]:
            score += 0.1

        return max(0.0, min(1.0, score))


class LanguageQualitySignal(QualitySignal):
    """Language and encoding quality"""

    def __init__(self):
        super().__init__(
            name="language_quality",
            weight=0.10,
            description="Language detection confidence and text encoding quality"
        )

    def compute(self, content: dict[str, Any], source: dict[str, Any],
                context: dict[str, Any]) -> float:
        """Compute language quality score"""

        text = content.get("text", "")
        language = content.get("language", "en")

        if not text:
            return 0.0

        score = 1.0

        # Language detection confidence
        try:
            from langdetect import detect_langs
            lang_probs = detect_langs(text)

            if lang_probs:
                # Check if detected language matches expected
                top_lang = lang_probs[0]
                if top_lang.lang == language:
                    score *= top_lang.prob
                else:
                    score *= 0.5  # Penalty for language mismatch
            else:
                score *= 0.3
        except:
            score *= 0.7  # Penalty for detection failure

        # Text quality checks
        if len(text) < 50:
            score *= 0.3

        # Check for encoding issues
        encoding_issues = [
            "�",  # Replacement character
            "â€™",  # Common encoding issue
            "â€œ",  # Another common issue
        ]

        for issue in encoding_issues:
            if issue in text:
                score *= 0.7
                break

        # Check for excessive repetition
        words = text.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # Too much repetition
                score *= 0.5

        return max(0.0, min(1.0, score))


class QualityScorer:
    """Main quality scoring engine"""

    def __init__(self, settings: Settings):
        self.settings = settings

        # Initialize quality signals
        self.signals = [
            SourceReputationSignal(),
            FreshnessSignal(),
            ContentDepthSignal(),
            TitleQualitySignal(),
            SportsRelevanceSignal(),
            LanguageQualitySignal(),
        ]

        # Validation
        total_weight = sum(signal.weight for signal in self.signals)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Signal weights sum to {total_weight}, not 1.0")

    def compute_quality_score(self, content: dict[str, Any], source: dict[str, Any],
                            context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Compute comprehensive quality score"""

        if context is None:
            context = {}

        signal_scores = {}
        weighted_sum = 0.0

        # Compute each signal
        for signal in self.signals:
            try:
                signal_value = signal.compute(content, source, context)
                signal_scores[signal.name] = {
                    "value": signal_value,
                    "weight": signal.weight,
                    "weighted_value": signal_value * signal.weight
                }
                weighted_sum += signal_value * signal.weight

            except Exception as e:
                logger.error(f"Error computing signal {signal.name}: {e}")
                signal_scores[signal.name] = {
                    "value": 0.0,
                    "weight": signal.weight,
                    "weighted_value": 0.0,
                    "error": str(e)
                }

        # Final quality score
        quality_score = max(0.0, min(1.0, weighted_sum))

        # Quality classification
        if quality_score >= self.settings.quality.premium_quality_threshold:
            quality_class = "premium"
        elif quality_score >= self.settings.quality.default_quality_threshold:
            quality_class = "good"
        elif quality_score >= self.settings.quality.min_quality_score:
            quality_class = "acceptable"
        else:
            quality_class = "poor"

        return {
            "quality_score": quality_score,
            "quality_class": quality_class,
            "signal_scores": signal_scores,
            "computed_at": datetime.utcnow().isoformat(),
            "algorithm_version": "1.0"
        }

    def should_accept_content(self, quality_result: dict[str, Any]) -> tuple[bool, str]:
        """Determine if content should be accepted based on quality"""

        quality_score = quality_result["quality_score"]

        # Shadow mode check
        if self.settings.quality.shadow_mode:
            # In shadow mode, always accept but log decisions
            would_reject = quality_score < self.settings.quality.default_quality_threshold

            if would_reject:
                logger.info(f"SHADOW MODE: Would reject content with quality {quality_score}")
                return True, f"shadow_mode_would_reject_{quality_score:.3f}"
            else:
                return True, f"shadow_mode_accept_{quality_score:.3f}"

        # Enforcement mode
        if quality_score < self.settings.quality.min_quality_score:
            return False, f"quality_too_low_{quality_score:.3f}"

        return True, f"quality_acceptable_{quality_score:.3f}"


class SourceReputationManager:
    """Manages source reputation based on quality feedback"""

    def __init__(self, settings: Settings):
        self.settings = settings

    def update_source_reputation(self, source_id: str, quality_scores: list[float],
                               error_rate: float = 0.0) -> dict[str, Any]:
        """Update source reputation based on recent quality scores"""

        if not quality_scores:
            return {"reputation_score": 0.5, "quality_tier": 2, "change": 0.0}

        # Calculate average quality
        avg_quality = sum(quality_scores) / len(quality_scores)

        # Calculate reputation score with decay
        decay_factor = 0.95  # Slight decay to encourage consistent quality
        current_reputation = avg_quality * decay_factor

        # Adjust for error rate
        error_penalty = min(0.3, error_rate * 0.5)
        current_reputation -= error_penalty

        # Determine quality tier
        if current_reputation >= 0.8 and error_rate < 0.05:
            quality_tier = 1  # Premium
        elif current_reputation >= 0.6 and error_rate < 0.15:
            quality_tier = 2  # Quality
        else:
            quality_tier = 3  # Discovery

        # Clamp reputation score
        reputation_score = max(
            self.settings.quality.min_reputation_score,
            min(self.settings.quality.max_reputation_score, current_reputation)
        )

        return {
            "reputation_score": reputation_score,
            "quality_tier": quality_tier,
            "avg_quality": avg_quality,
            "error_rate": error_rate,
            "sample_size": len(quality_scores),
            "updated_at": datetime.utcnow().isoformat()
        }

    def get_crawl_priority(self, source_reputation: dict[str, Any]) -> float:
        """Get crawl priority based on source reputation"""

        quality_tier = source_reputation.get("quality_tier", 2)
        reputation_score = source_reputation.get("reputation_score", 0.5)

        # Base priority by tier
        tier_priorities = {1: 1.0, 2: 0.7, 3: 0.4}
        base_priority = tier_priorities.get(quality_tier, 0.4)

        # Adjust by reputation score
        priority = base_priority * (0.5 + reputation_score * 0.5)

        return max(0.1, min(1.0, priority))


# Quality gate for content filtering
class QualityGate:
    """Quality gate for content filtering with shadow mode"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.scorer = QualityScorer(settings)
        self.reputation_manager = SourceReputationManager(settings)

        # Statistics
        self.stats = {
            "total_processed": 0,
            "accepted": 0,
            "rejected": 0,
            "shadow_would_reject": 0,
            "quality_scores": [],
        }

    def process_content(self, content: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
        """Process content through quality gate"""

        self.stats["total_processed"] += 1

        # Compute quality score
        quality_result = self.scorer.compute_quality_score(content, source)

        # Make acceptance decision
        should_accept, reason = self.scorer.should_accept_content(quality_result)

        # Update statistics
        self.stats["quality_scores"].append(quality_result["quality_score"])

        if should_accept:
            self.stats["accepted"] += 1
        else:
            self.stats["rejected"] += 1

        if "shadow_mode_would_reject" in reason:
            self.stats["shadow_would_reject"] += 1

        # Prepare result
        result = {
            "content": content,
            "quality_result": quality_result,
            "should_accept": should_accept,
            "decision_reason": reason,
            "processed_at": datetime.utcnow().isoformat()
        }

        return result

    def get_stats(self) -> dict[str, Any]:
        """Get quality gate statistics"""

        stats = self.stats.copy()

        if stats["quality_scores"]:
            scores = stats["quality_scores"]
            stats["avg_quality_score"] = sum(scores) / len(scores)
            stats["min_quality_score"] = min(scores)
            stats["max_quality_score"] = max(scores)

        if stats["total_processed"] > 0:
            stats["acceptance_rate"] = stats["accepted"] / stats["total_processed"]
            stats["rejection_rate"] = stats["rejected"] / stats["total_processed"]

            if self.settings.quality.shadow_mode:
                stats["shadow_rejection_rate"] = stats["shadow_would_reject"] / stats["total_processed"]

        return stats


# Example usage
async def main():
    """Example quality scoring usage"""


    settings = get_settings()
    quality_gate = QualityGate(settings)

    # Example content
    content = {
        "title": "Lakers Beat Warriors 120-115 in Overtime Thriller",
        "text": """The Los Angeles Lakers defeated the Golden State Warriors 120-115 in an
        overtime thriller at Crypto.com Arena on Monday night. LeBron James led the Lakers
        with 35 points and 12 assists, while Stephen Curry scored 42 points for the Warriors
        in the losing effort. The game was tied 110-110 at the end of regulation before the
        Lakers outscored the Warriors 10-5 in the extra period to secure the victory.""",
        "word_count": 65,
        "published_at": datetime.utcnow() - timedelta(hours=2),
        "language": "en",
        "sports_keywords": ["Lakers", "Warriors", "LeBron James", "Stephen Curry", "NBA"],
        "content_type": "game_recap"
    }

    # Example source
    source = {
        "name": "ESPN",
        "domain": "espn.com",
        "quality_tier": 1,
        "reputation_score": 0.85,
        "success_rate": 0.95
    }

    # Process content
    result = quality_gate.process_content(content, source)

    print(f"Quality score: {result['quality_result']['quality_score']:.3f}")
    print(f"Quality class: {result['quality_result']['quality_class']}")
    print(f"Should accept: {result['should_accept']}")
    print(f"Decision reason: {result['decision_reason']}")

    # Print signal breakdown
    for signal_name, signal_data in result["quality_result"]["signal_scores"].items():
        print(f"  {signal_name}: {signal_data['value']:.3f} (weight: {signal_data['weight']})")

    # Print statistics
    stats = quality_gate.get_stats()
    print(f"\nQuality gate stats: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
