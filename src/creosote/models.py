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
    top_level_import_names: Optional[List[str]] = None
    distlib_db_import_name: Optional[str] = None
    canonicalized_package_name: Optional[str] = None
    associated_imports: List[Import] = dataclasses.field(default_factory=list)
