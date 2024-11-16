# creosote

[![check](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/check.yml)
[![test](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml/badge.svg)](https://github.com/fredrikaverpil/creosote/actions/workflows/test.yml)

Identify unused dependencies and avoid a bloated virtual environment.

## 🌀 Migration guide: creosote 2.x to 3.x

<details>
<summary>Expand me to read the guide.</summary>

<br>Creosote was updated to 3.0.0 because the way arguments were supplied has
now changed. This also brings `pyproject.toml` configuration support.

### Argument name change

The argument naming has changed:

| 2.x argument name | 3.x argument name |
| ----------------- | ----------------- |
| `--exclude-deps`  | `--exclude-dep`   |
| `--paths`         | `--path`          |
| `--sections`      | `--section`       |

### Multiple argument values

With creosote 2.x, you were able to provide multiple values following some
arguments, example:

```bash
creosote -p file1.py file2.py
```

With creosote 3.x, you must now provide multiple arguments as a key/value pair:

```bash
creosote -p file1.py -p file2.py
```

This new creosote 3.x behavior applies to the following 3.x CLI arguments:

- `--venv`
- `--exclude-dep`
- `-p` or `--path`
- `-s` or `--section`

</details>

## ⚡️ Quickstart

Install creosote in separate virtual environment (using e.g.
[`pipx`](https://github.com/pypa/pipx)):

```bash
pipx install creosote
```

Scan virtual environment for unused dependencies
([PEP-621](https://peps.python.org/pep-0621/) example below, but
[Poetry](https://python-poetry.org/), [Pipenv](https://github.com/pypa/pipenv),
[PDM](https://pdm.fming.dev/latest/) and `requirements.txt` files are also
supported,
[see this table](#which-dependency-specification-toolingstandards-are-supported)):

```
$ creosote
Found dependencies in pyproject.toml: dotty-dict, loguru, pip-requirements-parser, requests, toml
Oh no, bloated venv! 🤢 🪣
Unused dependencies found: requests
```

And after having removed/uninstalled `requests`:

```
$ creosote
Found dependencies in pyproject.toml: dotty-dict, loguru, pip-requirements-parser, toml
No unused dependencies found! ✨
```

✋ Note that you will likely not be able to run `creosote` as-is, but will have
to configure it so it understands your project structure.

Get help:

```bash
creosote --help
```

## ⚙️ Configuration

You can configure creosote using commandline arguments or in your
`pyproject.toml`.

### Using commandline arguments

#### Required arguments

| Argument      | Default value                                    | Description                                                                                            |
| ------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `--venv`      | Path to activated virtual environment or `.venv` | The path(s) to your virtual environment or site-packages folder.                                       |
| `--path`      | `src`                                            | The path(s) to your source code, one or more files/folders.                                            |
| `--deps-file` | `pyproject.toml`                                 | The path to the file specifying your dependencies, like `pyproject.toml`, `requirements_*.txt \| .in`. |
| `--section`   | `project.dependencies`                           | The toml section(s) to parse, e.g. `project.dependencies`.                                             |

#### Optional arguments

| Argument        | Default value | Description                                                               |
| --------------- | ------------- | ------------------------------------------------------------------------- |
| `--exclude-dep` |               | Dependencies you wish to not scan for.                                    |
| `--format`      | `default`     | The output format, valid values are `default`, `no-color` or `porcelain`. |

### Using `pyproject.toml`

```toml
[tool.creosote]
venvs=[".venv"]
paths=["src"]
deps-file="pyproject.toml"
sections=["project.dependencies"]
exclude-deps =[
  "pyodbc",
  "pg8000",
]
```

## 🤔 How this works

The creosote tool will first scan the given python file(s) for all its imports.
Then it fetches all dependency names (from the dependencies spec file). Finally,
all imports are associated with their corresponding dependency name (requires
the virtual environment for resolving and the ability to read the dependency's
`RECORD` or `top_level.txt` file). If a dependency does not have any imports
associated, it is considered unused.

See the `main` function in
[`cli.py`](https://github.com/fredrikaverpil/creosote/blob/main/src/creosote/cli.py)
for a terse overview of the logic.

### 🌶️ Features

These optional features enable new/experimental functionality, that may be
backward incompatible and may be removed/changed at any time. Some features may
become mandatory for a target release version e.g. the next major release.
Enable using `--use-feature <FEATURE>`. Use at your own risk!

| Feature                           | Description                                                                                                                                                                                 | Target version |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `fail-excluded-and-not-installed` | When excluding a dependency from the scan (using `--exclude-dep`) and if the dependency is removed from the dependency specification file (e.g. `pyproject.toml`), return with exit code 1. | N/A            |

### 😤 Known limitations

- `importlib` imports are not detected by the AST parser (a great first
  contribution for anyone inclined 😄, reach out or start looking at
  `parsers.py:get_module_info_from_python_file`.

## 🥧 History and ambition

This project was inspired by security vulnerability reports about production
dependencies that were shipped into production but turned out to be unused.
Creosote aims to help prevent such occurrences and reduce noise from bots like
[Dependabot](https://github.com/dependabot) or
[Renovate](https://github.com/renovatebot/renovate) for simply unused
dependencies.

The intent is to run Creosote in CI (or with
[pre-commit](https://pre-commit.com)) to detect cases where developers forget to
remove unused dependencies, especially during refactorings. Creosote can
identify both unused production dependencies and developer dependencies,
depending on your objectives.

## 🤨 FAQ

### Which dependency specification tooling/standards are supported?

| Tool/standard                                                                                                               | Supported | `--deps-file` value | Example `--section` values                                                                                          |
| --------------------------------------------------------------------------------------------------------------------------- | :-------: | ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [PDM](https://pdm.fming.dev/latest/) and [PEP-582](https://peps.python.org/pep-0582/)                                       |    ✅     | `pyproject.toml`    | `project.dependencies`,<br>`project.optional-dependencies.<GROUP>`,<br>`tool.pdm.dev-dependencies`                  |
| [Pipenv](https://pipenv.pypa.io/en/latest/)                                                                                 |    ✅     | `pyproject.toml`    | `packages`,<br>`dev-packages`                                                                                       |
| [Poetry](https://python-poetry.org/)                                                                                        |    ✅     | `pyproject.toml`    | `tool.poetry.dependencies`,<br>`tool.poetry.dev-dependencies` (legacy),<br>`tool.poetry.group.<GROUP>.dependencies` |
| Legacy Setuptools (`setup.py`)                                                                                              |    ❌     |                     |                                                                                                                     |
| [PEP-508](https://peps.python.org/pep-0508/) (`requirements.txt`, [pip-tools](https://pip-tools.readthedocs.io/en/latest/)) |    ✅     | `*.[txt\|in]`       | N/A                                                                                                                 |
| [PEP-621](https://peps.python.org/pep-0621/)                                                                                |    ✅     | `pyproject.toml`    | `project.dependencies`,<br>`project.optional-dependencies.<GROUP>`                                                  |

#### 📔 Notes on [PEP-508](https://peps.python.org/pep-0508) (`requirements.txt`)

When using `requirements.txt` files to specify dependencies, there is no way to
tell which part of `requirements.txt` specifies production vs developer
dependencies. Therefore, you have to break your `requirements.txt` file into
e.g. `requirements-prod.txt` and `requirements-dev.txt` and use any of them as
input. When using [pip-tools](https://pip-tools.readthedocs.io/en/latest/), you
likely want to point Creosote to scan your `*.in` file(s).

#### 📓 Notes on [PEP-582](https://peps.python.org/pep-0582/) (`__pypackages__`)

Creosote supports the `__pypackages__` folder, although PEP-582 was rejected.
There is no reason to remove support for this today, but in case supporting this
becomes cumbersome in the future, supporting PEP-582 might be dropped.

```bash
creosote --venv __pypackages__
```

### Can I specify multiple toml sections?

Yes, you can specify a list of sections after the `--section` argument. It all
depends on what your setup looks like and what you set out to achieve.

```bash
$ creosote --section project.dependencies --section project.optional-dependencies.lint --section project.optional-dependencies.test
```

### Can I exclude dependencies from the scan?

Yes, you can use the `--exclude-dep` argument to specify one or more
dependencies you do not wish to get warnings for.

This feature is intended for dependencies you must specify in your dependencies
spec file, but which you don't import in your source code. An example of such a
dependency are database drivers, which are commonly only defined in connection
strings and will signal to the ORM which driver to use.

```bash
$ creosote --exclude-dep pyodbc --exclude-dep pg8000
```

### Can I run Creosote on Jupyter notebook (\*.ipynb) files?

Yes, any Jupyter notebook files will be temporarily converted to python files
using [nbconvert](https://github.com/jupyter/nbconvert) and then Creosote will
run on those.

### Can I run Creosote in a GitHub Action workflow?

Yes, please see the `action` job example in
[`.github/workflows/test.yml`](https://github.com/fredrikaverpil/creosote/blob/main/.github/workflows/test.yml).

### Can I run Creosote with [pre-commit](https://pre-commit.com)?

Yes, see example in
[`.pre-commit-config.yaml`](https://github.com/fredrikaverpil/creosote/blob/main/.pre-commit-config.yaml).

<details>
<summary>Here's another example setup, if already have Creosote installed onto $PATH (via e.g. pipx).</summary>

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: system
        name: creosote
        entry:
          creosote --venv .venv --path src --deps-file pyproject.toml --section
          project.dependencies
        pass_filenames: false
        files: \.(py|toml|txt|in|lock)$
        language: system
```

</details>

### What's with the name "creosote"?

This tool has borrowed its name from the
[Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).

## 📰 Creosote in the "news"

Because it makes me happy to see this tool can help others! 🥰

- [Creosote - Identify unused dependencies and avoid a bloated virtual environment](https://www.reddit.com/r/Python/comments/11n717z/creosote_identify_unused_dependencies_and_avoid_a/)
  — Reddit

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

You can also clone down the repo and run creosote from the git repo:

```bash
$ python -m venv .venv
$ source .venv/bin/activate  # linux/macOS syntax
$ pip install -e '.[dev]'  # install the dependencies group 'dev'
$ creosote -venv .venv ...
```

### 🚀 Releasing

1. Bump version in `src/creosote/__about__.py` and `.pre-commit-config.yaml`.
2. GitHub Action will run automatically on creating
   [a release](https://github.com/fredrikaverpil/creosote/releases) and deploy
   the release onto PyPi.
