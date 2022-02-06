class DepsReader:
    def __init__(self):
        self.packages = None

    @staticmethod
    def _pyproject():
        """Return production dependencies from pyproject.toml."""
        found_dependencies = []
        with open("pyproject.toml", "r") as infile:
            contents = infile.readlines()

        record = False
        for line in contents:
            if "poetry.dependencies" in line:
                record = True
                continue
            elif "[" in line:
                record = False

            if record is True and "=" in line:
                entry = line[: line.find("=")].strip()
                found_dependencies.append(entry)

        return sorted(found_dependencies)

    def read(self, deps_file):
        if deps_file == "pyproject.toml":
            self.packages = self._pyproject()
