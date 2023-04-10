import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class ImportInfo:
    module: List[str]
    name: List[str]
    alias: Optional[str] = None


@dataclasses.dataclass
class DependencyInfo:
    name: str  # as defined in the dependencies specification file
    top_level_import_names: Optional[List[str]] = None
    record_import_names: Optional[List[str]] = None
    canonicalized_dep_name: Optional[str] = None
    associated_imports: List[ImportInfo] = dataclasses.field(default_factory=list)
