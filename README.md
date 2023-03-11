# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml)
[![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml)

Identify unused dependencies and avoid a bloated virtual environment.

## :zap: Quickstart

Install creosote in separate virtual environment (using e.g. [`pipx`](https://github.com/pypa/pipx)):

```bash
pipx install creosote
```

Scan virtual environment for unused packages ([PEP-621](https://peps.python.org/pep-0621/) example below, but [Poetry](https://python-poetry.org/), [Pipenv](https://github.com/pypa/pipenv) and `requirements.txt` files are also supported, [see this table](#which-dependency-specification-toolingstandards-are-supported)):


```
$ creosote
Found packages in pyproject.toml: PyYAML, distlib, loguru, protobuf, toml
Oh no! 💥 💔 💥
Unused packages found: PyYAML, protobuf
```

And after having removed/uninstalled `PyYAML` and `protobuf`:

```
$ creosote
Found packages in pyproject.toml: distlib, loguru, toml
No unused packages found! ✨ 🍰 ✨
```

Get help:

```bash
creosote --help
```

## 🤔 How this works

Some data is required as input:

| Argument      | Default value          | Description                                                                                            |
| ------------- | ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `--venv`      | `.venv`                | The path to your virtual environment.                                                                  |
| `--paths`     | `src`                  | The path to your source code, one or more files/folders.                                               |
| `--deps-file` | `pyproject.toml`       | The path to the file specifying your dependencies, like `pyproject.toml`, `requirements_*.txt \| .in`. |
| `--sections`  | `project.dependencies` | One or more toml sections to parse, e.g. `project.dependencies`.                                       |


The creosote tool will first scan the given python file(s) for all its imports. Then it fetches all package names (from the dependencies spec file). Finally, all imports are associated with their corresponding package name (requires the virtual environment for resolving). If a package does not have any imports associated, it will be considered to be unused.

### :triumph: Known limitations

- `importlib` imports are not detected by the AST parser (a great first contribution for anyone inclined 😄, reach out or start [here](https://github.com/fredrikaverpil/creosote/blob/72d4ce0a8a983725a704decce9083702aa2312cc/src/creosote/parsers.py#L138-L156)).

## 🥧 History and ambition

The idea of a package like this was born from having gotten security vulnerability
reports about production dependencies (shipped into production) which turned out to not not
even be in use.

The goal would be to be able to run this tool in CI, which will catch cases where the developer
forgets to remove unused dependencies. An example of such a case could be when doing refactorings.

Note: The creosote tool supports identifying both unused production dependencies and developer dependencies. It all depends on what you would like to achieve.

## :raised_eyebrow: FAQ

### Which dependency specification tooling/standards are supported?

| Tool/standard                                                                                                               |     Supported      | `--deps-file` value | Example `--sections` values                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------- | :----------------: | ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [PEP-621](https://peps.python.org/pep-0621/) ⭐                                                                              | :white_check_mark: | `pyproject.toml`    | `project.dependencies`,<br>`project.optional-dependencies.<GROUP>`                                                  |
| [Poetry](https://python-poetry.org/)                                                                                        | :white_check_mark: | `pyproject.toml`    | `tool.poetry.dependencies`,<br>`tool.poetry.dev-dependencies` (legacy),<br>`tool.poetry.group.<GROUP>.dependencies` |
| [Pipenv](https://pipenv.pypa.io/en/latest/)                                                                                 | :white_check_mark: | `pyproject.toml`    | `packages`,<br>`dev-packages`                                                                                       |
| [PEP-508](https://peps.python.org/pep-0508/) (`requirements.txt`, [pip-tools](https://pip-tools.readthedocs.io/en/latest/)) | :white_check_mark: | `*.[txt\|in]`       | N/A                                                                                                                 |
| Legacy Setuptools (`setup.py`)                                                                                              |         ❌          |                     |                                                                                                                     |

#### 📔 Notes on [PEP-508](https://peps.python.org/pep-0508) (`requirements.txt`)

When using `requirements.txt` files to specify dependencies, there is no way to tell which part of `requirements.txt` specifies production vs developer dependencies. Therefore, you have to break your `requirements.txt` file into e.g. `requirements-prod.txt` and `requirements-dev.txt` and use any of them as input. When using [pip-tools](https://pip-tools.readthedocs.io/en/latest/), you likely want to point Creosote to scan your `*.in` file(s).

### Can I specify multiple toml sections?

Yes, you can specify a list of sections after the `--sections` argument. It all depends on what your setup looks like and what you set out to achieve.

### Can I run Creosote in a GitHub Action workflow?

Yes, please see the `action` job in [`.github/workflows/test.yml`](.github/workflows/test.yml) for a working example.

### Can I run Creosote with [pre-commit](https://pre-commit.com)?

Yes, you can either use Cresosote by specifying the exact, desired version (a very common workflow), or you can piggy-back on the Creosote already installed via e.g. `pipx`.

Examples:

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/fredrikaverpil/creosote
    rev: v2.3.5
    hooks:
      - id: creosote
        args:
          - "--venv=.venv"
          - "--paths=$MY_PROJECT_PATH"
          - "--deps-file=pyproject.toml"
          - "--sections=project.dependencies"
```

```yaml
# .pre-commit-config.yaml

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

### What's with the name "creosote"?

This tool has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).

## :woman_scientist: Development/debugging info
### Install in-development builds

You can run in-development versions of Creosote. Examples below:

```bash
# Creosote build from main branch
$ pipx install --suffix=@main --force git+https://github.com/fredrikaverpil/creosote.git@main
$ creosote@main --venv .venv ...
$ pipx uninstall creosote@main

# Creosote build from PR #123
$ pipx install --suffix=@123 --force git+https://github.com/fredrikaverpil/creosote.git@refs/pull/123/head
$ creosote@123 --venv .venv ...
$ pipx uninstall creosote@123
```

### Releasing

1. Bump version in `src/creosote/__about__.py`.
2. GitHub Action will run automatically on creating [a release](https://github.com/fredrikaverpil/creosote/releases) and deploy the release onto PyPi.
