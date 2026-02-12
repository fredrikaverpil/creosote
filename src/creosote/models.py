import dataclasses


@dataclasses.dataclass(slots=True)
class ImportInfo:
    module: list[str]
    name: list[str]
    alias: str | None = None

    @classmethod
    def from_module_name(cls, module_name: str) -> "ImportInfo":
        """Create ImportInfo from a simple module name (e.g., for Django apps)."""
        return cls(module=[], name=[module_name], alias=None)


@dataclasses.dataclass(slots=True)
class DependencyInfo:
    name: str  # as defined in the dependencies specification file
    top_level_import_names: list[str] | None = None
    record_import_names: list[str] | None = None
    canonicalized_dep_name: str | None = None
    associated_imports: list[ImportInfo] = dataclasses.field(default_factory=list)
