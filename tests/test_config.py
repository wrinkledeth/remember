import os
import tempfile
from pathlib import Path

from remember.config import find_config, load_config


def test_find_config_in_cwd(monkeypatch, tmp_path):
    config_file = tmp_path / "remember.toml"
    config_file.write_text('[remember]\ncards_dir = "./cards"\n')
    monkeypatch.chdir(tmp_path)
    assert find_config() == config_file


def test_find_config_walks_up(monkeypatch, tmp_path):
    config_file = tmp_path / "remember.toml"
    config_file.write_text('cards_dir = "./cards"\n')
    child = tmp_path / "sub" / "deep"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    assert find_config() == config_file


def test_find_config_returns_none(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert find_config() is None


def test_load_config_parses_toml(monkeypatch, tmp_path):
    config_file = tmp_path / "remember.toml"
    config_file.write_text('cards_dir = "./cards"\n')
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config["cards_dir"] == "./cards"


def test_load_config_empty_when_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config == {}
