import tomllib
from pathlib import Path


def find_config() -> Path | None:
    """Find remember.toml: check cwd upward, then project root as fallback."""
    # Walk up from cwd
    current = Path.cwd()
    for directory in [current, *current.parents]:
        candidate = directory / "remember.toml"
        if candidate.is_file():
            return candidate
    # Fallback: project root (two levels up from this file: config.py -> remember/ -> src/ -> project/)
    project_root = Path(__file__).resolve().parent.parent.parent
    candidate = project_root / "remember.toml"
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
