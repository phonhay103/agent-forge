"""Wrapper for google/magika library with Dependency Injection."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_MAGIKA_AVAILABLE = False
try:
    from magika import Magika, PredictionMode

    _MAGIKA_AVAILABLE = True
except ImportError:
    Magika = None  # type: ignore
    PredictionMode = None  # type: ignore
    logger.warning("google/magika library not installed.")


class MagikaWrapper:
    """Dependency Injection wrapper around google/magika."""

    def __init__(
        self, 
        magika_instance: Any | None = None, 
        model_dir: str | None = None,
        prediction_mode: str = "high_confidence",
    ) -> None:
        self._magika_instance = magika_instance

        if self._magika_instance is None and _MAGIKA_AVAILABLE and Magika is not None and PredictionMode is not None:
            try:
                # Map string to PredictionMode enum
                mode_enum = PredictionMode.HIGH_CONFIDENCE
                if prediction_mode == "medium_confidence":
                    mode_enum = PredictionMode.MEDIUM_CONFIDENCE
                elif prediction_mode == "best_guess":
                    mode_enum = PredictionMode.BEST_GUESS
                    
                if model_dir:
                    self._magika_instance = Magika(model_dir=model_dir, prediction_mode=mode_enum)
                else:
                    self._magika_instance = Magika(prediction_mode=mode_enum)
            except Exception as e:
                logger.warning(f"Failed to instantiate Magika: {e}")
                self._magika_instance = None

    @property
    def is_available(self) -> bool:
        """Returns True if native Magika library is instantiated."""
        return self._magika_instance is not None

    def identify_bytes(self, buffer: bytes) -> Any:
        """Identify buffer using Magika."""
        if self._magika_instance is not None:
            return self._magika_instance.identify_bytes(buffer)
        raise RuntimeError("google/magika library is not available.")

    def identify_path(self, file_path: str) -> Any:
        """Identify file path using Magika."""
        if self._magika_instance is not None:
            return self._magika_instance.identify_path(file_path)
        raise RuntimeError("google/magika library is not available.")

    def identify_paths(self, file_paths: list[str]) -> Any:
        """Identify multiple file paths using Magika batch processing."""
        if self._magika_instance is not None:
            from pathlib import Path
            paths = [Path(p) for p in file_paths]
            return self._magika_instance.identify_paths(paths)
        raise RuntimeError("google/magika library is not available.")
