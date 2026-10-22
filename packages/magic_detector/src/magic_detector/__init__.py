"""MagicDetector package export."""

from magika import ContentTypeLabel

from magic_detector._constants import DEFAULT_BINARY_MIME, UNINFORMATIVE_EXTENSIONS, UNINFORMATIVE_MIMES, UNKNOWN
from magic_detector.checkers import (
    CustomMagicChecker,
    MagicBytesChecker,
    MagicEncodingChecker,
    MagicExtensionChecker,
    MagicMimeChecker,
    MagikaChecker,
)
from magic_detector.client import MagicDetectorSuite
from magic_detector.enums import FileType
from magic_detector.factory import DetectorContainer, create_default_container
from magic_detector.interfaces import BaseChecker, BaseEnsembleStrategy, BasePipelineStrategy
from magic_detector.magic_wrapper import MagicWrapper
from magic_detector.magika_wrapper import MagikaWrapper
from magic_detector.models import DetectionResult, InputTarget, NormalizedResult
from magic_detector.normalizer import OutputNormalizer
from magic_detector.parallel import (
    CompositeEnsembleStrategy,
    ConsensusEnsembleStrategy,
    ConsensusMode,
    FirstMatchEnsembleStrategy,
    ParallelRunner,
    PrimaryCategoryEnsembleStrategy,
)
from magic_detector.pipeline import (
    FallbackChainStrategy,
    PipelineRunner,
    SequentialAccumulatorStrategy,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_BINARY_MIME",
    "UNINFORMATIVE_EXTENSIONS",
    "UNINFORMATIVE_MIMES",
    "UNKNOWN",
    "BaseChecker",
    "BaseEnsembleStrategy",
    "BasePipelineStrategy",
    "CompositeEnsembleStrategy",
    "ConsensusEnsembleStrategy",
    "ConsensusMode",
    "ContentTypeLabel",
    "CustomMagicChecker",
    "DetectionResult",
    "DetectorContainer",
    "FallbackChainStrategy",
    "FileType",
    "FirstMatchEnsembleStrategy",
    "InputTarget",
    "MagicBytesChecker",
    "MagicDetectorSuite",
    "MagicEncodingChecker",
    "MagicExtensionChecker",
    "MagicMimeChecker",
    "MagicWrapper",
    "MagikaChecker",
    "MagikaWrapper",
    "NormalizedResult",
    "OutputNormalizer",
    "ParallelRunner",
    "PipelineRunner",
    "PrimaryCategoryEnsembleStrategy",
    "SequentialAccumulatorStrategy",
    "create_default_container",
]
