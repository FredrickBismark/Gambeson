"""Pipeline orchestrator: config → geometry → mesh → solve → visualize.

Each stage is independently callable. The orchestrator chains them together
and handles file routing between stages.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Modern Gambeson simulation pipeline orchestrator",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/armor_config.yaml"),
        help="Path to armor configuration YAML",
    )
    parser.add_argument(
        "--size",
        choices=["S", "M", "L", "XL", "XXL"],
        default="M",
        help="Size grade to generate (default: M)",
    )
    parser.add_argument(
        "--stage",
        choices=["geometry", "mesh", "static", "thermal", "impact", "postprocess", "all"],
        default="all",
        help="Pipeline stage to run (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for generated files",
    )
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pipeline stage={args.stage} size={args.size} config={args.config}")
    print("Pipeline stages not yet implemented — see ROADMAP.md Phase 1-2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
