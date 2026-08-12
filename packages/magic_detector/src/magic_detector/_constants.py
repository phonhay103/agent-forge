"""Internal constants for magic_detector package. No custom enums."""

# Explicit unknown type label — returned when detection fails or is inconclusive
UNKNOWN: str = "unknown"

# Generic/uninformative MIME types used for filtering in strategies
UNINFORMATIVE_MIMES: frozenset[str] = frozenset({
    "application/octet-stream",
    "text/plain",
    "inode/x-empty",
    "application/x-empty",
    "unknown/unknown",
    UNKNOWN,
})

# Generic/uninformative file extensions used for filtering
UNINFORMATIVE_EXTENSIONS: frozenset[str] = frozenset({
    "txt",
    "bin",
    "dat",
    "tmp",
    "out",
    UNKNOWN,
})

# Default MIME fallback
DEFAULT_BINARY_MIME: str = "application/octet-stream"
