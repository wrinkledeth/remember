import tomllib
from pathlib import Path


def find_config() -> Path | None:
    """Walk up from cwd looking for remember.toml."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        candidate = directory / "remember.toml"
        if candidate.is_file():
            return candidate
    return None


def load_config() -> dict:
    """Load remember.toml if it exists. Returns empty dict if not found."""
    path = find_config()
    if path is None:
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)
