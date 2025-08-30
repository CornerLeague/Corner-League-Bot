# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Content ingestion and crawling library."""

__version__ = "1.0.0"

from .extractor import (
    CanonicalURLExtractor,
    ContentExtractor,
    ContentHasher,
    DuplicateDetector,
    ExtractionPipeline,
    NearDuplicateDetector,
    URLCanonicalizer,
)

__all__ = [
    "CanonicalURLExtractor",
    "ContentExtractor",
    "ContentHasher",
    "DuplicateDetector",
    "ExtractionPipeline",
    "NearDuplicateDetector",
    "URLCanonicalizer",
    "__version__",
]
