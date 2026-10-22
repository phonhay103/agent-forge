"""Parallel package export."""

from magic_detector.parallel.runner import ParallelRunner
from magic_detector.parallel.strategies import (
    CompositeEnsembleStrategy,
    ConsensusEnsembleStrategy,
    ConsensusMode,
    FirstMatchEnsembleStrategy,
    PrimaryCategoryEnsembleStrategy,
)

__all__ = [
    "CompositeEnsembleStrategy",
    "ConsensusEnsembleStrategy",
    "ConsensusMode",
    "FirstMatchEnsembleStrategy",
    "ParallelRunner",
    "PrimaryCategoryEnsembleStrategy",
]
