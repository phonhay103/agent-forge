"""Wrapper for python-magic with Dependency Injection."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import official python-magic
_MAGIC_AVAILABLE = False
try:
    # Optional dependency: python-magic ships only via the `magic` extra, so the
    # module is unresolvable in a default environment.
    import magic  # ty: ignore[unresolved-import]

    # Check if libmagic underlying shared library is actually loaded
    try:
        m_test = magic.Magic()
        _MAGIC_AVAILABLE = True
    except Exception as e:
        logger.warning(f"python-magic imported but libmagic library failed to load: {e}.")
except ImportError:
    magic = None
    logger.warning("python-magic module not installed.")


class MagicWrapper:
    """Dependency Injection wrapper around python-magic."""

    def __init__(
        self,
        magic_instance: Any | None = None,
        mime: bool = False,
        mime_encoding: bool = False,
        uncompress: bool = False,
        magic_file: str | None = None,
        raw: bool = False,
        keep_going: bool = False,
    ) -> None:
        self.mime = mime
        self.mime_encoding = mime_encoding
        self.uncompress = uncompress
        self.magic_file = magic_file
        self.raw = raw
        self.keep_going = keep_going
        self._magic_instance = magic_instance

        # Initialize magic instance if python-magic is available and not injected
        if self._magic_instance is None and _MAGIC_AVAILABLE and magic is not None:
            try:
                self._magic_instance = magic.Magic(
                    mime=self.mime,
                    mime_encoding=self.mime_encoding,
                    uncompress=self.uncompress,
                    magic_file=self.magic_file,
                    raw=self.raw,
                    keep_going=self.keep_going,
                )
            except Exception as e:
                logger.warning(f"Failed to create magic.Magic instance: {e}")
                self._magic_instance = None

    @property
    def is_native_available(self) -> bool:
        """Return True if native python-magic with C libmagic is active."""
        return self._magic_instance is not None

    def from_buffer(self, buffer: bytes) -> str:
        """Inspect bytes buffer using magic."""
        if self._magic_instance is not None:
            return self._magic_instance.from_buffer(buffer)
        raise RuntimeError("libmagic library is not available.")

    def from_file(self, file_path: str) -> str:
        """Inspect file path using magic."""
        if self._magic_instance is not None:
            return self._magic_instance.from_file(file_path)
        raise RuntimeError("libmagic library is not available.")
