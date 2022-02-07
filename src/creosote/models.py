import dataclasses
from typing import Optional


@dataclasses.dataclass
class Import:
    module: list[str]
    name: list[str]
    alias: Optional[str] = None


@dataclasses.dataclass
class Package:
    name: str
    top_level_names: Optional[list[str]] = None
    module_name: Optional[str] = None
    importable_as: Optional[str] = None
    associated_imports: list[Import] = dataclasses.field(default_factory=list)
