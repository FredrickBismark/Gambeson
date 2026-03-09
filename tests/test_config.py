"""Tests for config loading and validation."""

from __future__ import annotations

from pathlib import Path

import yaml


CONFIG_DIR = Path(__file__).parent.parent / "config"


def test_armor_config_loads() -> None:
    path = CONFIG_DIR / "armor_config.yaml"
    assert path.exists(), f"Missing {path}"
    data = yaml.safe_load(path.read_text())
    assert "sizes" in data
    assert "M" in data["sizes"]


def test_materials_config_loads() -> None:
    path = CONFIG_DIR / "materials.yaml"
    assert path.exists(), f"Missing {path}"
    data = yaml.safe_load(path.read_text())
    assert "materials" in data
    assert "HDPE" in data["materials"]


def test_simulation_params_loads() -> None:
    path = CONFIG_DIR / "simulation_params.yaml"
    assert path.exists(), f"Missing {path}"
    data = yaml.safe_load(path.read_text())
    assert "solver" in data or "load_cases" in data
