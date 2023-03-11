# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml)
[![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml)

Identify unused dependencies and avoid a bloated virtual environment.

## Quickstart

Install creosote in separate virtual environment (using e.g. [pipx](https://github.com/pypa/pipx)):

```bash
pipx install creosote
```

Scan virtual environment for unused packages ([PEP-621](https://peps.python.org/pep-0621/) example below, but [Poetry](https://python-poetry.org/), [Pipenv](https://github.com/pypa/pipenv) and `requirements.txt` files are also supported):

```bash
creosote --venv .venv --paths src --deps-file pyproject.toml --sections project.dependencies
```

Example output (using Poetry dependency definition):

```bash
$ creosote --venv .venv --paths src --deps-file pyproject.toml --sections tool.poetry.dependencies
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

- The path to the virtual environment (`--venv`).
- The path to one or more Python files, or a folder containing such files (`--paths`).
- A list of package names, fetched from e.g. `pyproject.toml`, `requirements_*.txt|.in` (`--deps-file`).
- One or more toml sections to parse, e.g. `project.dependencies` (`--sections`).

The creosote tool will first scan the given python file(s) for all its imports. Then it fetches all package names (from the dependencies spec file). Finally, all imports are associated with their corresponding package name (requires the virtual environment for resolving). If a package does not have any imports associated, it will be considered to be unused.

## Ambition and history

The idea of a package like this was born from having gotten security vulnerability
reports about production dependencies (shipped into production) which turned out to not not
even be in use.

The goal would be to be able to run this tool in CI, which will catch cases where the developer
forgets to remove unused dependencies. An example of such a case could be when doing refactorings.

Note: The creosote tool supports identifying both unused production dependencies and developer dependencies.

## FAQ

### Are requirements.txt files supported?

Yes, kind of. There is no way to tell which part of `requirements.txt` specifies production vs developer dependencies. Therefore, you have to break your `requirements.txt` file into e.g. `requirements-prod.txt` and `requirements-dev.txt` and use any of them as input.

If you are using [pip-tools](https://github.com/jazzband/pip-tools), you can provide a `*.in` file.

### Can I scan for PEP-621 dependencies?

Yes! Just provide `--sections project.dependencies`.

### Can I scan for PEP-621 optional dependencies?

Yes! Just provide `--sections project.optional-dependencies.<GROUP>` where `<GROUP>` is your dependency group name, e.g. `--sections project.optional-dependencies.lint`.

### Can I scan for Poetry's dependencies?

Yes, see below!

#### Main dependencies

Just provide `--sections tool.poetry.dependencies`.

#### Dev-dependencies?

Just provide `--sections tool.poetry.dev-dependencies`.

#### Dependency groups?

Just provide `--sections tool.poetry.group.<GROUP>.dependencies` where `<GROUP>` is your dependency group, e.g. `--sections tool.poetry.group.lint.dependencies`.

### Can I scan for Pipenv dependencies?

Yes, see below!

#### Dependencies

Just provide `--sections packages`.

#### Developer dependencies

Just provide `--sections dev-packages`.

### Can I scan for multiple toml sections?

Yes! Just provide each section after the `--sections` parameter, e.g. `--sections project.optional-dependencies.test project.optional-dependencies.lint`.

### Can I use this as a GitHub Action?

Yes! See the `action` job in [.github/workflows/test.yml](.github/workflows/test.yml) for a working example.

### Can I use this with [pre-commit](https://pre-commit.com)?

Yes, please refer to [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml). You can also configure pre-commit to run creosote if it is available on `$PATH` (e.g. if you installed it with `pipx`). Example below:

```yaml
repos:
  - repo: local
    hooks:
      - id: system
        name: creosote
        entry: creosote --venv .venv --paths src --deps-file pyproject.toml --sections project.dependencies
        pass_filenames: false
        files: \.(py|toml|txt|in|lock)$
        language: system
```

### 💡 Install in-development builds

You can run in-development versions of Creosote. Examples below:

```bash
# Creosote build from main branch
$ pipx install --suffix=@main --force git+https://github.com/fredrikaverpil/creosote.git
$ creosote@main --venv .venv ...
$ pipx uninstall creosote@main

# Creosote build from PR #123
$ pipx install --suffix=@123 --force git+https://github.com/fredrikaverpil/creosote.git@refs/pull/123/head
$ creosote@123 --venv .venv ...
$ pipx uninstall creosote@123
```

### What's with the name "creosote"?

This tool has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).


### Releasing

1. Bump version in `src/creosote/__about__.py`.
2. GitHub Action will run automatically on creating [a release](https://github.com/fredrikaverpil/creosote/releases) and deploy the release onto PyPi.
