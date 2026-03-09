"""Parametric body geometry generator using CadQuery.

Generates a simplified torso form and stacks the 6-layer armor system
as concentric offset shells. Each layer is a separate solid body
exported as STEP for downstream FEA meshing.

Usage:
    python -m src.geometry.generate --config config/armor_config.yaml --size M
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import cadquery as cq

    HAS_CADQUERY = True
except ImportError:
    HAS_CADQUERY = False

from src.geometry.config_loader import ArmorConfig, load_config


def make_torso_base(config: ArmorConfig) -> "cq.Workplane":
    """Create a simplified torso base shape as a rounded box.

    The torso is modeled as a box with rounded edges, sized from
    the chest pattern width and torso height. This is the innermost
    surface (body side) onto which armor layers are stacked.

    Returns:
        CadQuery Workplane with the base torso solid.
    """
    if not HAS_CADQUERY:
        raise ImportError("CadQuery is required for geometry generation. pip install cadquery")

    # Half-dimensions for the torso cross-section
    chest_half = config.chest_pattern_width / 2
    # Approximate front-to-back depth as 70% of width (typical torso ratio)
    depth_half = chest_half * 0.70
    height = config.torso_height

    # Create rounded box torso form
    # Fillet radius for body-like rounding (25mm)
    fillet_r = 25.0

    torso = (
        cq.Workplane("XY")
        .box(chest_half * 2, depth_half * 2, height, centered=(True, True, False))
        .edges("|Z")
        .fillet(fillet_r)
    )

    return torso


def make_layer_shell(
    base_shape: "cq.Shape",
    inner_offset: float,
    thickness: float,
    tolerance: float = 0.01,
) -> "cq.Shape":
    """Create a single armor layer as an offset shell.

    Uses makeOffsetShape() to create concentric shells. Falls back to
    a simpler box expansion if offset fails on sharp features.

    Args:
        base_shape: The base torso OCCT Shape.
        inner_offset: Cumulative offset to inner surface of this layer.
        thickness: Layer thickness in mm.
        tolerance: OCCT offset tolerance.

    Returns:
        CadQuery Shape representing the layer solid.
    """
    try:
        outer = base_shape.makeOffsetShape(inner_offset + thickness, tolerance)
        inner = base_shape.makeOffsetShape(inner_offset, tolerance)
        layer = outer.cut(inner)
        return layer
    except Exception:
        # Fallback: cannot offset this shape, skip gracefully
        raise RuntimeError(
            f"Offset failed at offset={inner_offset}, thickness={thickness}. "
            "Try simplifying the base geometry or reducing fillet radii."
        )


def make_flat_panel_layer(
    width: float,
    depth: float,
    height: float,
    inner_offset: float,
    thickness: float,
) -> "cq.Workplane":
    """Fallback: create a flat panel layer via box extrusion.

    Used when makeOffsetShape() fails on complex geometry.
    Each layer is a slightly larger box minus a slightly smaller box.
    """
    if not HAS_CADQUERY:
        raise ImportError("CadQuery required")

    expand = inner_offset
    outer_expand = inner_offset + thickness

    outer = (
        cq.Workplane("XY")
        .box(
            width + outer_expand * 2,
            depth + outer_expand * 2,
            height + outer_expand * 2,
            centered=(True, True, False),
        )
        .translate((0, 0, -outer_expand))
    )
    inner = (
        cq.Workplane("XY")
        .box(
            width + expand * 2,
            depth + expand * 2,
            height + expand * 2,
            centered=(True, True, False),
        )
        .translate((0, 0, -expand))
    )

    return outer.cut(inner)


def generate_armor_layers(
    config: ArmorConfig,
    use_offset: bool = True,
) -> list[tuple[str, str, "cq.Workplane"]]:
    """Generate all armor layers as separate CadQuery solids.

    Args:
        config: Resolved armor configuration.
        use_offset: If True, use makeOffsetShape. If False, use flat panels.

    Returns:
        List of (layer_name, material_name, solid) tuples.
    """
    if not HAS_CADQUERY:
        raise ImportError("CadQuery required")

    chest_w = config.chest_pattern_width
    depth = chest_w * 0.70
    height = config.torso_height

    results: list[tuple[str, str, cq.Workplane]] = []
    cumulative_offset = 0.0

    if use_offset:
        base_wp = make_torso_base(config)
        base_shape = base_wp.val()

        for layer in config.layers:
            try:
                layer_shape = make_layer_shell(
                    base_shape, cumulative_offset, layer.thickness
                )
                layer_wp = cq.Workplane("XY").newObject([layer_shape])
                results.append((layer.name, layer.material, layer_wp))
            except RuntimeError:
                # Fall back to flat panel for this layer
                panel = make_flat_panel_layer(
                    chest_w, depth, height, cumulative_offset, layer.thickness
                )
                results.append((layer.name, layer.material, panel))
            cumulative_offset += layer.thickness
    else:
        for layer in config.layers:
            panel = make_flat_panel_layer(
                chest_w, depth, height, cumulative_offset, layer.thickness
            )
            results.append((layer.name, layer.material, panel))
            cumulative_offset += layer.thickness

    return results


def export_layers(
    layers: list[tuple[str, str, "cq.Workplane"]],
    output_dir: Path,
    combined: bool = True,
) -> list[Path]:
    """Export armor layers as STEP files.

    Args:
        layers: Output from generate_armor_layers().
        output_dir: Directory for STEP files.
        combined: If True, also export a combined assembly STEP.

    Returns:
        List of exported file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for i, (name, _material, solid) in enumerate(layers):
        path = output_dir / f"layer_{i + 1}_{name}.step"
        cq.exporters.export(solid, str(path))
        paths.append(path)

    if combined and len(layers) > 1:
        assembly = cq.Assembly()
        for name, material, solid in layers:
            assembly.add(solid, name=f"{name}_{material}")
        combined_path = output_dir / "armor_assembly.step"
        assembly.save(str(combined_path))
        paths.append(combined_path)

    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate parametric armor geometry",
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config/armor_config.yaml"),
    )
    parser.add_argument(
        "--size", choices=["S", "M", "L", "XL", "XXL"], default="M",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output/geometry"),
    )
    parser.add_argument(
        "--flat-panels", action="store_true",
        help="Use flat panel extrusion instead of offset shells",
    )
    args = parser.parse_args(argv)

    if not HAS_CADQUERY:
        print("Error: CadQuery not installed. pip install cadquery", file=sys.stderr)
        return 1

    config = load_config(args.config, args.size)
    print(f"Generating armor geometry: size={config.size}")
    print(f"  Chest width: {config.chest_pattern_width} mm")
    print(f"  Torso height: {config.torso_height:.0f} mm")
    print(f"  Total layer thickness: {config.total_layer_thickness:.1f} mm")
    print(f"  Layers: {len(config.layers)}")

    layers = generate_armor_layers(config, use_offset=not args.flat_panels)
    paths = export_layers(layers, args.output_dir)

    print(f"\nExported {len(paths)} STEP files to {args.output_dir}/")
    for p in paths:
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
