# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yaml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yaml) [![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yaml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yaml)

Identify unused dependencies and avoid a bloated virtual environment.

## Quickstart

Install creosote in separate virtual environment (using e.g. [pipx](https://github.com/pypa/pipx)):

```bash
pipx install creosote
```

Scan virtual environment for unused packages:

```bash
creosote --deps-file pyproject.toml --venv .venv --paths src
```

Example output:

```bash
$ creosote
Parsing src/creosote/formatters.py
Parsing src/creosote/models.py
Parsing src/creosote/resolvers.py
Parsing src/creosote/__init__.py
Parsing src/creosote/parsers.py
Parsing src/creosote/cli.py
Parsing pyproject.toml for packages
Found packages in pyproject.toml: PyYAML, distlib, loguru, protobuf, toml
Resolving...
Unused packages found: PyYAML, protobuf
```

Get help:

```bash
creosote --help
```

## How this works

Some data is required as input:

- A list of package names (fetched from e.g. `pyproject.toml`, `requirements_*.txt|.in`)
- The path to the virtual environment
- The path to one or more Python files

The creosote tool will first scan the given python file(s) for all its imports. Then it fetches all package names. Finally, all imports are associated with their corresponding package name. If a package does not have any imports associated, it will be considered to be unused.

## Ambition and history

The idea of a package like this was born from having gotten security vulnerability
reports about production dependencies (shipped into production) which turned out to not not
even be in use.

The goal would be to be able to run this tool in CI, which will catch cases where the developer
forgets to remove unused packages. A example of such a case could be when doing refactorings.

This can work well in tandem with flake8 or pylint, which can warn in CI about unused imports.

Note: The creosote tool supports identifying both unused production dependencies and developer dependencies.

## FAQ

### Are requirements.txt files supported?

Yes, kind of. There is no way to tell which part of `requirements.txt` specifies production vs developer dependencies. Therefore, you have to break your `requirements.txt` file into e.g. `requirements-prod.txt` and `requirements-dev.txt` and use any of them as input.

If you are using [pip-tools](https://github.com/jazzband/pip-tools), you can provide a `*.in` file.

### Can I scan for pyproject's dev-dependencies?

Yes! For `pyproject.toml`, just provide the `--dev` argument.

### Can I use this as a GitHub Action?

Yes! See [.github/workflows/action.yaml](.github/workflows/action.yaml) for a working example.

### What's with the name "creosote"?

This library has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).
