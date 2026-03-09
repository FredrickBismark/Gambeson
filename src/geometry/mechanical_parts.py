"""SolidPython2 wrappers for OpenSCAD mechanical parts.

Provides Python functions that generate OpenSCAD code for:
- V-groove rail track
- Helmet attachment rail
- HDPE skeleton plates (collar, yokes, spine segments, lumbar bridge)

Each function returns a SolidPython2 object that can be rendered to .scad
or exported to .stl via the OpenSCAD CLI.

Usage:
    python -m src.geometry.mechanical_parts --part rail_track --size M --output output/
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from solid2 import cube, cylinder, difference, hull, import_scad, polygon
    from solid2 import linear_extrude, rotate, rotate_extrude, translate, union
    from solid2 import scad_render_to_file

    HAS_SOLIDPYTHON = True
except ImportError:
    HAS_SOLIDPYTHON = False

from src.geometry.config_loader import ArmorConfig, load_config

# Size grading lookup (matches OpenSCAD files)
SIZE_TABLE: dict[str, dict[str, float]] = {
    "S":   {"neck_r": 110, "chest_w": 420, "torso_h": 419},
    "M":   {"neck_r": 120, "chest_w": 440, "torso_h": 445},
    "L":   {"neck_r": 125, "chest_w": 460, "torso_h": 470},
    "XL":  {"neck_r": 130, "chest_w": 480, "torso_h": 496},
    "XXL": {"neck_r": 135, "chest_w": 500, "torso_h": 521},
}

SIZE_INDEX: dict[str, int] = {"S": 0, "M": 1, "L": 2, "XL": 3, "XXL": 4}


def render_openscad_part(
    scad_file: str,
    output_path: Path,
    size: str = "M",
    part: str = "assembly",
    extra_vars: dict[str, Any] | None = None,
) -> Path:
    """Render an OpenSCAD file to STL using the openscad CLI.

    Args:
        scad_file: Name of the .scad file in models/ directory.
        output_path: Output .stl file path.
        size: Size grade (S/M/L/XL/XXL).
        part: Part selector variable value.
        extra_vars: Additional OpenSCAD variables to set.

    Returns:
        Path to the rendered STL file.
    """
    models_dir = Path(__file__).parent.parent.parent / "models"
    scad_path = models_dir / scad_file

    if not scad_path.exists():
        raise FileNotFoundError(f"OpenSCAD file not found: {scad_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "openscad",
        "-o", str(output_path),
        "-D", f"size_index={SIZE_INDEX[size]}",
    ]

    if part:
        cmd.extend(["-D", f'part="{part}"'])

    if extra_vars:
        for key, val in extra_vars.items():
            if isinstance(val, str):
                cmd.extend(["-D", f'{key}="{val}"'])
            else:
                cmd.extend(["-D", f"{key}={val}"])

    cmd.append(str(scad_path))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"OpenSCAD render failed:\n{result.stderr}"
        )

    return output_path


def render_all_parts(
    size: str = "M",
    output_dir: Path | None = None,
) -> list[Path]:
    """Render all mechanical parts for a given size.

    Returns list of generated STL file paths.
    """
    if output_dir is None:
        output_dir = Path("output/mechanical")
    output_dir.mkdir(parents=True, exist_ok=True)

    parts: list[tuple[str, str, str]] = [
        ("rail_track.scad", "rail_track", ""),
        ("helmet_rail.scad", "helmet_rail", ""),
        ("skeleton_plates.scad", "collar", "collar"),
        ("skeleton_plates.scad", "yoke_left", "yoke"),
        ("skeleton_plates.scad", "spine_segment", "spine"),
        ("skeleton_plates.scad", "lumbar_bridge", "lumbar"),
        ("skeleton_plates.scad", "skeleton_assembly", "assembly"),
    ]

    paths = []
    for scad_file, name, part in parts:
        out = output_dir / f"{name}_{size}.stl"
        try:
            render_openscad_part(scad_file, out, size=size, part=part)
            paths.append(out)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"Warning: skipped {name}: {e}", file=sys.stderr)

    return paths


def generate_v_groove_profile_scad(
    groove_angle: float = 90.0,
    groove_depth: float = 6.0,
    track_width: float = 55.0,
    track_depth: float = 18.0,
    wall_thick: float = 4.0,
) -> str:
    """Generate OpenSCAD code for V-groove cross-section profile.

    Returns OpenSCAD polygon code as a string for embedding.
    """
    half_groove = groove_depth * math.tan(math.radians(groove_angle / 2))
    half_width = track_width / 2

    points = [
        (-half_width, track_depth),
        (-half_width, 0),
        (-half_groove, 0),
        (0, -groove_depth),
        (half_groove, 0),
        (half_width, 0),
        (half_width, track_depth),
    ]

    point_str = ", ".join(f"[{x:.1f}, {y:.1f}]" for x, y in points)
    return f"polygon(points=[{point_str}]);"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render OpenSCAD mechanical parts to STL",
    )
    parser.add_argument(
        "--part",
        choices=["rail_track", "helmet_rail", "collar", "yoke", "spine", "lumbar", "all"],
        default="all",
    )
    parser.add_argument(
        "--size", choices=["S", "M", "L", "XL", "XXL"], default="M",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output/mechanical"),
    )
    args = parser.parse_args(argv)

    if args.part == "all":
        paths = render_all_parts(args.size, args.output)
        print(f"Rendered {len(paths)} parts to {args.output}/")
        for p in paths:
            print(f"  {p.name}")
    else:
        scad_map = {
            "rail_track": ("rail_track.scad", ""),
            "helmet_rail": ("helmet_rail.scad", ""),
            "collar": ("skeleton_plates.scad", "collar"),
            "yoke": ("skeleton_plates.scad", "yoke"),
            "spine": ("skeleton_plates.scad", "spine"),
            "lumbar": ("skeleton_plates.scad", "lumbar"),
        }
        scad_file, part = scad_map[args.part]
        out = args.output / f"{args.part}_{args.size}.stl"
        render_openscad_part(scad_file, out, size=args.size, part=part)
        print(f"Rendered {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
