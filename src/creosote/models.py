import dataclasses
from typing import Optional


@dataclasses.dataclass
class ImportInfo:
    module: list[str]
    name: list[str]
    alias: Optional[str] = None

    @classmethod
    def from_module_name(cls, module_name: str) -> "ImportInfo":
        """Create ImportInfo from a simple module name (e.g., for Django apps)."""
        return cls(module=[], name=[module_name], alias=None)


@dataclasses.dataclass
class DependencyInfo:
    name: str  # as defined in the dependencies specification file
    top_level_import_names: Optional[list[str]] = None
    record_import_names: Optional[list[str]] = None
    canonicalized_dep_name: Optional[str] = None
    associated_imports: list[ImportInfo] = dataclasses.field(default_factory=list)
