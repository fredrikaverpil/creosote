# creosote

Prevent bloated virtual environments by identifing installed, but unused, dependencies.

## Quickstart

```bash
# Activate your virtual environment
$ . .venv/bin/activate

# Install creosote in your virtual environment
$ pip install creosote

# Scan activated virtual environment for unused packages
$ creosote -p path/to/folder/**/*.py -d pyproject.toml
```

## Future improvements

- It would be great if creosote wouldn't have to rely on the activated virtual environment. This could also enable installing creosote with e.g. pipx, outside the virtual environment of interest.

## Ambition and history

The idea of a package like this was born from having gotten security vulnerability
reports about dependencies (shipped into production) which turned out to not not
even be in use.

The goal would be to be able to run this tool in CI, which will catch cases where the developer
forgets to remove unused packages. A example of such a case could be when doing refactorings.

This can work well in tandem with flake8 or pylint, which can warn in CI about unused imports.

## What's with the name "creosote"?

This library has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).
