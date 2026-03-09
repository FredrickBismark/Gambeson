"""Tests for config loading and geometry generation.

CadQuery-dependent tests are skipped if CadQuery is not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.geometry.config_loader import ArmorConfig, load_config


CONFIG_PATH = Path(__file__).parent.parent / "config" / "armor_config.yaml"


def test_load_config_default_size() -> None:
    config = load_config(CONFIG_PATH, "M")
    assert config.size == "M"
    assert config.chest_pattern_width == 440
    assert config.waist_pattern_width == 360
    assert config.neck_arc_radius == 120


def test_load_config_all_sizes() -> None:
    for size in ["S", "M", "L", "XL", "XXL"]:
        config = load_config(CONFIG_PATH, size)
        assert config.size == size
        assert config.chest_pattern_width > 0
        assert len(config.layers) == 6


def test_layer_stack() -> None:
    config = load_config(CONFIG_PATH, "M")
    assert len(config.layers) == 6
    # Verify all 6 layers in order (body → exterior)
    assert config.layers[0].name == "spacer_mesh"
    assert config.layers[0].material == "spacer_mesh_3d"
    assert config.layers[1].name == "cotton_batting"
    assert config.layers[2].name == "hdpe_skeleton"
    assert config.layers[2].thickness == 6.0
    assert config.layers[3].name == "impact_foam"
    assert config.layers[4].name == "quilted_batting"
    assert config.layers[5].name == "outer_shell"


def test_total_thickness() -> None:
    config = load_config(CONFIG_PATH, "M")
    total = config.total_layer_thickness
    # spacer(4) + batting(20) + hdpe(6) + foam(10) + quilted(12) + shell(0.8) = 52.8
    assert abs(total - 52.8) < 0.01


def test_skeleton_dimensions() -> None:
    config = load_config(CONFIG_PATH, "M")
    sk = config.skeleton
    assert sk.collar_arc_radius == 120
    assert sk.collar_arc_length == 200
    assert sk.spine_segment_count == 4
    assert sk.yoke_length == 200
    assert sk.lumbar_width == 200


def test_torso_height() -> None:
    config = load_config(CONFIG_PATH, "M")
    # Average of [432, 457]
    assert abs(config.torso_height - 444.5) < 0.1


def test_invalid_size() -> None:
    with pytest.raises(ValueError, match="Unknown size"):
        load_config(CONFIG_PATH, "XXXL")


def test_size_grading_monotonic() -> None:
    """Key dimensions should increase with size."""
    sizes = ["S", "M", "L", "XL", "XXL"]
    configs = [load_config(CONFIG_PATH, s) for s in sizes]
    for i in range(1, len(configs)):
        assert configs[i].chest_pattern_width > configs[i - 1].chest_pattern_width
        assert configs[i].waist_pattern_width > configs[i - 1].waist_pattern_width
        assert configs[i].torso_height > configs[i - 1].torso_height
        assert configs[i].neck_arc_radius >= configs[i - 1].neck_arc_radius
