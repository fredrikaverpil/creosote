# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml)
[![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml)

Identify unused dependencies and avoid a bloated virtual environment.

## ⚡️ Quickstart

Install creosote in separate virtual environment (using e.g. [`pipx`](https://github.com/pypa/pipx)):

```bash
pipx install creosote
```

Scan virtual environment for unused dependencies ([PEP-621](https://peps.python.org/pep-0621/) example below, but [Poetry](https://python-poetry.org/), [Pipenv](https://github.com/pypa/pipenv) and `requirements.txt` files are also supported, [see this table](#which-dependency-specification-toolingstandards-are-supported)):


```
$ creosote
Found dependencies in pyproject.toml: distlib, dotty-dict, loguru, pip-requirements-parser, requests, toml
Oh no, bloated venv! 🤢 🪣
Unused dependencies found: requests
```

And after having removed/uninstalled `requests`:

```
$ creosote
Found dependencies in pyproject.toml: distlib, dotty-dict, loguru, pip-requirements-parser, toml
No unused dependencies found! ✨
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


The creosote tool will first scan the given python file(s) for all its imports. Then it fetches all dependency names (from the dependencies spec file). Finally, all imports are associated with their corresponding dependency name (requires the virtual environment for resolving). If a dependency does not have any imports associated, it is considered unused.

See the `main` function in [`cli.py`](https://github.com/fredrikaverpil/creosote/blob/main/src/creosote/cli.py) for a terse overview of the logic.

### 😤 Known limitations

- `importlib` imports are not detected by the AST parser (a great first contribution for anyone inclined 😄, reach out or start [here](https://github.com/fredrikaverpil/creosote/blob/72d4ce0a8a983725a704decce9083702aa2312cc/src/creosote/parsers.py#L138-L156)).

## 🥧 History and ambition

The idea of a project like this was hatched from having security vulnerability
reports about production dependencies (shipped into production) which turned out to not not
even be in use.

This can also help avoiding noise from bots like [Dependabot](https://github.com/dependabot) or [Renovate](https://github.com/renovatebot/renovate)
for dependencies you don't even need.

The goal of this project is to run the `creosote` tool in CI, which will catch cases where the developer
forgets to remove unused dependencies. An example of such a case could be when doing refactorings.

Note: Creosote supports identifying both unused production dependencies and developer dependencies. It all depends on what you would like to achieve.

## 🤨 FAQ

### Which dependency specification tooling/standards are supported?

| Tool/standard                                                                                                               |     Supported      | `--deps-file` value | Example `--sections` values                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------- | :----------------: | ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [PDM](https://pdm.fming.dev/latest/)                                                                                        | :white_check_mark: | `pyproject.toml`    | `project.dependencies`,<br>`project.optional-dependencies.<GROUP>`,<br>`tool.pdm.dev-dependencies`                  |   
| [PEP-621](https://peps.python.org/pep-0621/)                                                                                | :white_check_mark: | `pyproject.toml`    | `project.dependencies`,<br>`project.optional-dependencies.<GROUP>`                                                  |
| [Poetry](https://python-poetry.org/)                                                                                        | :white_check_mark: | `pyproject.toml`    | `tool.poetry.dependencies`,<br>`tool.poetry.dev-dependencies` (legacy),<br>`tool.poetry.group.<GROUP>.dependencies` |
| [Pipenv](https://pipenv.pypa.io/en/latest/)                                                                                 | :white_check_mark: | `pyproject.toml`    | `packages`,<br>`dev-packages`                                                                                       |
| [PEP-508](https://peps.python.org/pep-0508/) (`requirements.txt`, [pip-tools](https://pip-tools.readthedocs.io/en/latest/)) | :white_check_mark: | `*.[txt\|in]`       | N/A                                                                                                                 |
| Legacy Setuptools (`setup.py`)                                                                                              |         ❌          |                     |                                                                                                                     |

#### 📔 Notes on [PEP-508](https://peps.python.org/pep-0508) (`requirements.txt`)

When using `requirements.txt` files to specify dependencies, there is no way to tell which part of `requirements.txt` specifies production vs developer dependencies. Therefore, you have to break your `requirements.txt` file into e.g. `requirements-prod.txt` and `requirements-dev.txt` and use any of them as input. When using [pip-tools](https://pip-tools.readthedocs.io/en/latest/), you likely want to point Creosote to scan your `*.in` file(s).

### Can I specify multiple toml sections?

Yes, you can specify a list of sections after the `--sections` argument. It all depends on what your setup looks like and what you set out to achieve.

```bash
$ creosote --sections project.dependencies project.optional-dependencies.lint project.optional-dependencies.test
```

### Can I exclude dependencies from the scan?

Yes, you can use the `--exclude-deps` argument to specify one or more dependencies you do not wish to get warnings for.

This feature is intended for dependencies you must specify in your dependencies spec file, but which you don't import in your source code. An example of such a dependency are database drivers, which are commonly only defined in connection strings and will signal to the ORM which driver to use.

```bash
$ creosote --exclude-deps pyodbc starlette
```

### Can I run Creosote in a GitHub Action workflow?

Yes, please see the `action` job example in [`.github/workflows/test.yml`](https://github.com/fredrikaverpil/creosote/blob/main/.github/workflows/test.yml).

### Can I run Creosote with [pre-commit](https://pre-commit.com)?

Yes, see example in [`.pre-commit-config.yaml`](https://github.com/fredrikaverpil/creosote/blob/main/.pre-commit-config.yaml).


<details>
<summary>Here's another example setup, if already have Creosote installed onto $PATH (via e.g. pipx).</summary>

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

</details>


### What's with the name "creosote"?

This tool has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).

## 📰 Creosote in the "news"

Because it makes me happy to see this tool can help others! 🥰

- [Creosote - Identify unused dependencies and avoid a bloated virtual environment](https://www.reddit.com/r/Python/comments/11n717z/creosote_identify_unused_dependencies_and_avoid_a/) — Reddit


## 👩‍🔬 Development/debugging info

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
### 🚀 Releasing

1. Bump version in `src/creosote/__about__.py` and `.pre-commit-config.yaml`.
2. GitHub Action will run automatically on creating [a release](https://github.com/fredrikaverpil/creosote/releases) and deploy the release onto PyPi.
