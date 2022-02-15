import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class Import:
    module: List[str]
    name: List[str]
    alias: Optional[str] = None


@dataclasses.dataclass
class Package:
    name: str
    top_level_names: Optional[List[str]] = None
    module_name: Optional[str] = None
    importable_as: Optional[str] = None
    associated_imports: List[Import] = dataclasses.field(default_factory=list)
