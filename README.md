# creosote

Prevent bloated virtual environments by identifing installed packages, unused by your code.

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

- It would be great if creosote could be installed outside the virtual environment (e.g. via pipx), and wouldn't have to rely on it.

## What's with the name?

This library has borrowed its name from the [Monty Python scene about Mr. Creosote](https://www.youtube.com/watch?v=aczPDGC3f8U).
