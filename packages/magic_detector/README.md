# MagicDetector

The primary goal of the `magic-detector` package is to maintain **a single, highly robust parallel pipeline** that executes multiple file detection engines concurrently and intelligently ensembles their results. 

By running tools like Google's deep-learning-based `magika` alongside traditional deterministic heuristic engines like `libmagic` in parallel, this package eliminates the brittleness of relying on a single detector and delivers industry-standard accuracy for file type identification.

## Core Features
- **Parallel Ensemble Pipeline**: The flagship feature of this package. It runs all registered checkers simultaneously to minimize latency, then merges the results using a sophisticated ensemble strategy.
- **Adaptive Hybrid Ensembling**: Ships with an `AdaptiveHybridEnsembleStrategy` that implements industry best practices—relying on AI (Magika) for ambiguous text and source code, while trusting deterministic signatures (`libmagic`) for well-known binaries.
- **Graceful Fallback**: `magika` acts as the primary dependency. If the system lacks C-level libraries (`libmagic`), the parallel pipeline continues to function seamlessly with available checkers.

## Quick Start
```python
from magic_detector import MagicDetectorSuite

suite = MagicDetectorSuite()
# Executes all checkers in parallel and applies the AdaptiveHybrid ensemble strategy
result = suite.detect_parallel("path/to/file.ext")

print(f"MIME: {result.mime_type}")
print(f"Confidence: {result.confidence}")
```
