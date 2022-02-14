# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yaml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yaml) [![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yaml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yaml)

Identify unused production dependencies and avoid a bloated virtual environment.

## Quickstart

```bash
# Install creosote in separate virtual environment
$ pipx install creosote

# Scan virtual environment for unused packages
$ creosote -d pyproject.toml -v .venv -p path/to/folder/**/*.py

# Get help
$ creosote --help
```

## Creosote as GitHub Action

See [.github/workflows/action.yaml] for a working example.

## How this works

Some data is required as input:

- A list of production package names (can be fetched from e.g. `pyproject.toml`)
- The path to the virtual environment
- The path to one or more Python files

The creosote tool will first scan the given python file(s) for all its imports. Then it fetches all production package names. Finally, all imports are associated with their corresponding package name. If a package does not have any imports associated, it will be considered to be unused.

## Ambition and history

The idea of a package like this was born from having gotten security vulnerability
reports about dependencies (shipped into production) which turned out to not not
even be in use.

The goal would be to be able to run this tool in CI, which will catch cases where the developer
forgets to remove unused packages. A example of such a case could be when doing refactorings.

This can work well in tandem with flake8 or pylint, which can warn in CI about unused imports.

## What's with the name "creosote"?

This library has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).

## Future improvement ideas

- Support nicer inputs for `--paths`, don't require `*.py`. Ideally, default the argument to `src`.
- Add more tests
- Add support for requirements.txt
- Use toml to parse pyproject.toml
