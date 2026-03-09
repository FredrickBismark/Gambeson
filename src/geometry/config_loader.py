"""Load and resolve armor configuration for a specific size.

Reads config/armor_config.yaml and returns resolved dimensions
for a given size grade (S/M/L/XL/XXL).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LayerSpec:
    """Specification for a single armor layer."""

    name: str
    material: str
    thickness: float  # mm, resolved default

    @classmethod
    def from_config(cls, entry: dict[str, Any]) -> LayerSpec:
        thickness = entry.get("thickness") or entry.get("thickness_default", 0.0)
        return cls(
            name=entry["name"],
            material=entry["material"],
            thickness=float(thickness),
        )


@dataclass
class SkeletonSpec:
    """Resolved skeleton component dimensions."""

    collar_arc_radius: float
    collar_arc_length: float
    collar_width: float
    collar_substrate_thickness: float
    collar_padding_thickness: float
    yoke_length: float
    yoke_width_shoulder: float
    yoke_width_taper: float
    yoke_thickness: float
    spine_segment_count: int
    spine_segment_width: float
    spine_segment_height: float
    spine_segment_thickness: float
    spine_overlap: float
    lumbar_width: float
    lumbar_height: float
    lumbar_thickness: float
    hip_belt_width: float


@dataclass
class ArmorConfig:
    """Fully resolved armor configuration for a single size."""

    size: str
    chest_pattern_width: float
    waist_pattern_width: float
    chest_circumference: tuple[float, float]
    torso_length: tuple[float, float]
    neck_arc_radius: float
    layers: list[LayerSpec]
    skeleton: SkeletonSpec
    quilting_spacing: float
    seam_allowance: float
    chest_ease: float

    @property
    def total_layer_thickness(self) -> float:
        return sum(layer.thickness for layer in self.layers)

    @property
    def torso_height(self) -> float:
        """Average torso length for geometry generation."""
        return (self.torso_length[0] + self.torso_length[1]) / 2


def load_config(
    config_path: Path | None = None,
    size: str = "M",
) -> ArmorConfig:
    """Load armor config and resolve for a specific size.

    Args:
        config_path: Path to armor_config.yaml. Defaults to config/armor_config.yaml.
        size: Size grade — one of S, M, L, XL, XXL.

    Returns:
        Fully resolved ArmorConfig for the given size.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "armor_config.yaml"

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if size not in data["sizes"]:
        raise ValueError(f"Unknown size '{size}'. Valid: {list(data['sizes'].keys())}")

    sz = data["sizes"][size]
    sk = data["skeleton"]

    layers = [LayerSpec.from_config(entry) for entry in data["layers"]]

    collar_arc_radius = sz.get("neck_arc_radius", 120)
    if sk["collar"]["arc_radius"] is not None:
        collar_arc_radius = sk["collar"]["arc_radius"]

    skeleton = SkeletonSpec(
        collar_arc_radius=collar_arc_radius,
        collar_arc_length=sk["collar"]["arc_length"],
        collar_width=sk["collar"]["width"],
        collar_substrate_thickness=sk["collar"]["substrate_thickness"],
        collar_padding_thickness=sk["collar"]["padding_thickness"],
        yoke_length=sk["shoulder_yoke"]["length"],
        yoke_width_shoulder=sk["shoulder_yoke"]["width_shoulder"],
        yoke_width_taper=sk["shoulder_yoke"]["width_taper"],
        yoke_thickness=sk["shoulder_yoke"]["thickness"],
        spine_segment_count=sk["spine_plate"]["segment_count"],
        spine_segment_width=sk["spine_plate"]["segment_width"],
        spine_segment_height=sk["spine_plate"]["segment_height"],
        spine_segment_thickness=sk["spine_plate"]["segment_thickness"],
        spine_overlap=sk["spine_plate"]["overlap"],
        lumbar_width=sk["lumbar_bridge"]["width"],
        lumbar_height=sk["lumbar_bridge"]["height"],
        lumbar_thickness=sk["lumbar_bridge"]["thickness"],
        hip_belt_width=sk["hip_belt"]["width"],
    )

    return ArmorConfig(
        size=size,
        chest_pattern_width=sz["chest_pattern_width"],
        waist_pattern_width=sz["waist_pattern_width"],
        chest_circumference=tuple(sz["chest_circumference"]),
        torso_length=tuple(sz["torso_length"]),
        neck_arc_radius=collar_arc_radius,
        layers=layers,
        skeleton=skeleton,
        quilting_spacing=data["quilting"]["spacing"],
        seam_allowance=data["construction"]["seam_allowance"],
        chest_ease=data["construction"]["chest_ease"],
    )
