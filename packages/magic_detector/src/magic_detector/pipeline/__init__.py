"""Pipeline package export."""

from magic_detector.pipeline.runner import PipelineRunner
from magic_detector.pipeline.strategies import (
    FallbackChainStrategy,
    SequentialAccumulatorStrategy,
)

__all__ = [
    "FallbackChainStrategy",
    "PipelineRunner",
    "SequentialAccumulatorStrategy",
]
