# Modern Gambeson System

Integrated passive exoskeleton architecture with ball bearing rail helmet interface.
Open-source protective soft armor for civilian applications with DIY manufacturability.

## Project Overview

This project combines two parallel workstreams:

1. **Physical Design** — A modern gambeson (quilted textile armor) with an integrated HDPE skeleton that transfers load from shoulders to hips, plus a novel ball bearing rail helmet interface that decouples helmet rotation from collar movement.

2. **Simulation Pipeline** — A parametric CAD + FEA pipeline for modeling, meshing, and simulating the multi-layer armor system using open-source tools.

## Repository Structure

```
Gambeson/
├── CLAUDE.md                                          # This file
├── ROADMAP.md                                         # Development roadmap
├── Modern_Gambeson_System_Whitepaper.md               # Full technical whitepaper
├── compass_artifact_wf-*_text_markdown.md             # Simulation pipeline research
├── config/                                            # Parametric config (YAML)
│   ├── armor_config.yaml                              # Dimensions, size grading
│   ├── materials.yaml                                 # Material property database
│   └── simulation_params.yaml                         # Solver settings, load cases
├── src/
│   ├── geometry/                                      # CAD generation (CadQuery)
│   ├── simulation/                                    # FEA setup (CalculiX, Elmer, OpenRadioss)
│   ├── postprocessing/                                # Results → VTK → PyVista
│   └── pipeline/                                      # End-to-end orchestrator
├── patterns/                                          # Sewing patterns (DXF/SVG)
├── models/                                            # OpenSCAD mechanical parts
├── materials/                                         # .FCMat cards, .inp blocks
├── docker/                                            # Headless FreeCAD/solver env
├── tests/                                             # Validation & regression
└── output/                                            # Generated STEP, meshes, results
```

## Key Technical Decisions

- **CadQuery** over raw FreeCAD scripting for geometry generation (cleaner API, pip-installable, native STEP export)
- **OpenSCAD + BOSL2** for mechanical parts (ball bearing rail, HDPE skeleton plates, spine segments)
- **SolidPython2** as the Python→OpenSCAD bridge
- **CalculiX** for static structural analysis (shoulder loads, compression, HDPE plate buckling)
- **Elmer FEM** for thermal analysis (body heat through the 6-layer stack)
- **OpenRadioss** for impact/dynamic simulation (the only credible open-source explicit dynamics solver)
- **PrePoMax** as FEA pre/post-processor when GUI intervention is needed
- **Gmsh** for meshing; **meshio** for format conversion; **PyVista** for visualization
- YAML-driven configuration for all parametric dimensions, materials, and solver settings

## Material Stack (body → exterior)

| Layer | Material | Thickness | Role |
|-------|----------|-----------|------|
| 1 | 3D spacer mesh | 3–6 mm | Ventilation |
| 2 | Cotton batting | 15–25 mm | Comfort, initial energy absorption |
| 3 | HDPE skeleton | 6 mm | Load distribution, attachment infrastructure |
| 4 | EVA + D3O foam | 6–15 mm | Primary impact absorption |
| 5 | Quilted batting | 10–15 mm | Secondary absorption, garment structure |
| 6 | CORDURA shell | 0.5–1 mm | Abrasion, cut resistance |

## Simulation Unit System

CalculiX uses mm/N/s/K internally:
- Density: tonnes/mm³ (e.g., HDPE = 9.5e-7)
- Conductivity: mW/(mm·K)
- Forces: Newtons (verify — some FreeCAD API calls use millinewtons)
- Always use second-order elements (C3D10, 10-node tetrahedra)

## Code Conventions

- Python 3.10+, type hints everywhere
- Files ≤ 300 lines; split into focused modules
- Isolate FreeCAD imports to a single setup module (`src/geometry/freecad_setup.py`)
- Each pipeline stage is an independently callable Python function
- Config-driven: no hardcoded dimensions or material properties in source
- `subprocess` calls for solver invocation (ccx, ElmerSolver, OpenRadioss CLI)

## Key Commands

```bash
# Geometry generation
python -m src.geometry.generate --config config/armor_config.yaml --size M

# Run static structural analysis
python -m src.simulation.static --config config/simulation_params.yaml

# Run thermal analysis
python -m src.simulation.thermal --config config/simulation_params.yaml

# Full pipeline
python -m src.pipeline.orchestrator --config config/armor_config.yaml

# Render OpenSCAD mechanical parts
openscad -o output/rail_track.stl models/rail_track.scad -D 'size_index=2'
```

## Size Grading

Five sizes (S through XXL) driven by lookup tables in `config/armor_config.yaml`:
- S: chest 420 mm pattern width
- M: chest 440 mm
- L: chest 460 mm
- XL: chest 480 mm
- XXL: chest 500 mm

## Protection Targets

- CE Level 1 equivalent blunt force (EN 1621, <18 kN transmitted at 5 J)
- EN 388 Level A–B cut resistance (Level C–D with optional Kevlar)
- 60–70% load transfer from shoulders to hips
- System weight: 2.5–3.5 kg (skeleton + gambeson)
- Supported load: 15–30 kg additional equipment

## Ball Bearing Rail Helmet Interface

The core innovation: a semi-circular V-groove bearing track (~200 mm arc, ~120 mm radius) mounted on a rigid HDPE collar substrate. Helmet rotates freely on V-groove wheels while the collar stays stationary. Three bearing options documented (V-groove wheels for DIY, polymer plain bearings for production, curved linear guides for demos).

## Interoperability Notes

- OpenSCAD cannot export STEP natively — use CSG → FreeCAD import → STEP export
- `hull()` and `minkowski()` not supported in FreeCAD CSG import
- Multi-material FEM requires `Part::BooleanFragments` in CompSolid mode for conforming mesh interfaces
- Foam materials (EVA, D3O) require `*HYPERFOAM` constitutive model, not linear elastic
- D3O rate-dependent behavior needs `*HYPERFOAM` + `*VISCOELASTIC` with Prony series
