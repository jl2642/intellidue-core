from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PACKAGE_FORMAT_VERSION = "1.0.0"
DEFAULT_MAX_ENTRIES = 10_000
DEFAULT_MAX_TOTAL_UNCOMPRESSED = 1_073_741_824
DEFAULT_MAX_MEMBER_UNCOMPRESSED = 268_435_456
DEFAULT_MAX_COMPRESSION_RATIO = 200.0
DEFAULT_MAX_NESTED_DEPTH = 2


@dataclass(frozen=True)
class PackageLimits:
    max_entries: int = DEFAULT_MAX_ENTRIES
    max_total_uncompressed: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED
    max_member_uncompressed: int = DEFAULT_MAX_MEMBER_UNCOMPRESSED
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO
    max_nested_depth: int = DEFAULT_MAX_NESTED_DEPTH

    def __post_init__(self) -> None:
        if self.max_entries <= 0 or self.max_total_uncompressed <= 0 or self.max_member_uncompressed <= 0:
            raise ValueError("package size and entry limits must be positive")
        if self.max_compression_ratio <= 0 or self.max_nested_depth < 0:
            raise ValueError("compression ratio must be positive and nested depth cannot be negative")


@dataclass(frozen=True)
class PackageInspection:
    path: str
    package_type: str
    profile: str
    root: str | None
    entries: int
    total_uncompressed: int
    nested_archives: int
    descriptor: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
