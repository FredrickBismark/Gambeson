# Modern Gambeson System — Development Roadmap

## Vision

An open-source, DIY-manufacturable protective garment that integrates medieval quilted armor principles with modern materials science, a passive exoskeleton skeleton for hip-based load transfer, and a ball bearing rail helmet interface. Backed by a fully open-source parametric simulation pipeline for iterating designs computationally before physical builds.

---

## Phase 0: Project Foundation (Current)

**Goal:** Establish repository, documentation, and development environment.

- [x] Technical whitepaper (v1.0)
- [x] Simulation pipeline research document
- [x] CLAUDE.md project context
- [x] Development roadmap (this document)
- [x] Choose open hardware license (CERN-OHL-S-2.0)
- [x] Set up Python project scaffolding (`pyproject.toml`, linting, CI)
- [x] Create `config/` YAML schema for armor parameters, materials, and simulation settings
- [x] Set up Docker environment for headless FreeCAD + solvers
- [x] Create GitHub issue templates (bug, design proposal, build report, material test)

**Deliverables:** Buildable dev environment, project governance docs

---

## Phase 1: Material Database & Parametric Geometry

**Goal:** Machine-readable material library and scriptable CAD geometry for the full armor stack.

### 1A — Material Library

- [ ] Create `materials.yaml` with all 7 layer materials (spacer mesh, cotton batting, HDPE, EVA foam, D3O, quilted batting, CORDURA)
- [ ] Create `.FCMat` material cards for FreeCAD FEM integration
- [ ] Create CalculiX `.inp` material blocks (with correct mm/N/s/K unit conversions)
  - Linear elastic: HDPE, CORDURA (orthotropic), spacer mesh
  - Hyperfoam: EVA (Ogden N=1, μ₁≈1.25 MPa, α₁≈2.0)
  - Hyperfoam + viscoelastic: D3O approximation (Prony series from polyurethane literature)
- [ ] Document material sources and data provenance
- [ ] Validation: cross-check density, modulus, conductivity against MatWeb/MakeItFrom

### 1B — Parametric Body Geometry (CadQuery)

- [ ] Implement base torso shape generator from size-graded measurements (S–XXL)
- [ ] Implement `makeOffsetShape()` layer stacking for the 6-layer armor cross-section
- [ ] Flat panel extrusion fallback for zones where offset fails on sharp features
- [ ] STEP export for each layer as separate solid body
- [ ] Size grading driven by `config/armor_config.yaml` lookup tables

### 1C — Mechanical Parts (OpenSCAD + BOSL2)

- [ ] V-groove rail track: 200 mm arc, parametric radius, V-groove cross-section via `path_sweep()`
- [ ] Helmet attachment rail segment (matching V-groove profile)
- [ ] HDPE skeleton plates: collar, shoulder yokes, spine segments (×4), lumbar bridge
- [ ] Articulation joints between spine segments (overlap + webbing channels)
- [ ] NopSCADlib integration for ball bearings, fasteners, rod end bearings
- [ ] SolidPython2 wrapper scripts for all OpenSCAD models
- [ ] CSG → FreeCAD → STEP conversion script

**Deliverables:** Complete parametric geometry pipeline generating STEP assemblies for any size

---

## Phase 2: Simulation Infrastructure

**Goal:** Working FEA pipelines for static structural, thermal, and impact analysis.

### 2A — Meshing Pipeline

- [ ] Gmsh meshing script: STEP → `.msh` with size controls per layer
- [ ] `Part::BooleanFragments` (CompSolid mode) for conforming multi-material interfaces
- [ ] Mesh refinement at skeleton-to-foam boundaries and quilting stitch lines
- [ ] Second-order tetrahedral elements (C3D10) throughout
- [ ] meshio format conversion utilities (`.msh` → `.inp`, `.msh` → `.vtu`)
- [ ] Mesh quality validation checks (aspect ratio, Jacobian)

### 2B — Static Structural Analysis (CalculiX)

- [ ] Shoulder yoke load case: 300 N (≈30 kg) force on yoke contact faces
- [ ] Hip belt load transfer verification
- [ ] HDPE plate buckling analysis (spine segments under axial compression)
- [ ] Collar substrate stress under helmet bearing loads (5 kg helmet + accessories)
- [ ] PyCCX or pygccx integration for scripted `.inp` generation and solver invocation
- [ ] Results extraction: von Mises stress, displacement, reaction forces

### 2C — Thermal Analysis (Elmer FEM)

- [ ] Steady-state heat transfer through 6-layer stack
  - Body-side BC: 310.15 K (37°C skin temperature)
  - Outer-side BC: convective, h = 5–25 W/m²K, T_ambient = 293 K
- [ ] Per-layer thermal conductivity from `materials.yaml`
- [ ] pyelmer scripted `.sif` file generation
- [ ] Transient thermal analysis: time-to-equilibrium for donning scenario
- [ ] Temperature distribution visualization across layers

### 2D — Impact Simulation (OpenRadioss)

- [ ] Export mesh in OpenRadioss-compatible format (via PrePoMax or direct conversion)
- [ ] 5 J impact case matching CE Level 1 test conditions (2 kg mass, 26 cm drop)
- [ ] Hyperfoam material cards for EVA and D3O layers
- [ ] Contact definition between impactor and outer shell
- [ ] Transmitted force extraction at body-side surface
- [ ] Multi-hit degradation study (5 sequential impacts)

### 2E — Post-Processing & Visualization

- [ ] PyVista headless rendering pipeline (`Plotter(off_screen=True)`)
- [ ] Per-layer stress/temperature contour plots
- [ ] Deformation animation for impact events
- [ ] Automated report generation (results summary + images)
- [ ] VTK output for ParaView interactive exploration

**Deliverables:** Three validated simulation workflows (structural, thermal, impact) runnable end-to-end from config

---

## Phase 3: Pattern Engineering & Physical Prototyping

**Goal:** Generate sewing patterns and build the first physical prototype.

### 3A — Sewing Pattern Generation

- [ ] Parametric pattern generator (Python → DXF/SVG) for all gambeson panels
- [ ] Grande assiette armscye geometry (deeper than standard, historical validation)
- [ ] Forward-positioned underarm gores
- [ ] Zone-specific quilting patterns:
  - Diamond/lozenge at 35 mm spacing for chest/back
  - Horizontal lines at elbows
  - Vertical lines at torso sides
- [ ] Seam allowances and notch marks
- [ ] Size grading (S–XXL) with 2–4" chest ease
- [ ] Printable tiled output for home printers + plotter output

### 3B — Skeleton Fabrication Drawings

- [ ] HDPE cutting templates (DXF) for all skeleton components
- [ ] Heat-forming temperature and curvature specifications
- [ ] Drill patterns for bolt holes and webbing attachment
- [ ] Assembly sequence with hardware BOM (M5/M6 button-head bolts, nylon lock nuts, washers)
- [ ] Forming jig drawings for consistent production

### 3C — Bearing Rail Fabrication

- [ ] V-groove track bending guide (aluminum angle → ~120 mm radius arc)
- [ ] V-groove wheel mounting bracket design
- [ ] Retention lip design to prevent wheel disengagement
- [ ] Quick-release helmet detent mechanism
- [ ] Assembly and alignment procedure

### 3D — First Physical Build

- [ ] Complete DIY build following construction sequence (Phases 1–6 from whitepaper §8.2)
- [ ] Document build with photos at each stage
- [ ] Record actual build time per phase
- [ ] Note deviations from design, problem areas, and solutions
- [ ] Produce build report as template for community builders

**Deliverables:** First physical prototype, complete build documentation, pattern files for all sizes

---

## Phase 4: Testing & Validation

**Goal:** Comparative testing against commercial armor products.

### 4A — Impact Testing

- [ ] Build drop test rig (PVC guide tube, 2 kg impactor, clay backing)
- [ ] Test at 5 J (CE Level 1 energy), 10 J, 24 J
- [ ] Compare against commercial CE Level 1 motorcycle armor (D3O, SAS-TEC)
- [ ] Multi-hit testing: 5 impacts at same location, measure degradation
- [ ] Correlate physical test results with simulation predictions

### 4B — Bearing System Testing

- [ ] Rotation friction: qualitative comparison vs. velcro/zipper interfaces
- [ ] Load capacity: progressive weight test up to 5+ kg on helmet
- [ ] Retention: lateral and upward disengagement forces
- [ ] Durability: 10,000-cycle rotation test

### 4C — Fit & Mobility Testing

- [ ] Range of motion assessment (14 movements, 1–5 restriction scale)
- [ ] Extended wear test (72-hour protocol: 4–8 hours/day over 3 days)
- [ ] Hot-spot and chafing documentation
- [ ] Donning/doffing timing (target: <3 min don, <15 sec emergency doff)

### 4D — Environmental Testing

- [ ] Wet performance (submersion → impact and mobility retest)
- [ ] Cold performance (4 hours at -10°C → immediate test)
- [ ] UV exposure (24-hour sunlight → inspection and retest)

### 4E — Simulation Validation

- [ ] Compare simulated transmitted force vs. physical drop test measurements
- [ ] Compare simulated thermal profile vs. thermocouple measurements in prototype
- [ ] Calibrate material models based on physical test data
- [ ] Document simulation accuracy and limitations

**Deliverables:** Test result dataset, simulation validation report, design improvement recommendations

---

## Phase 5: Design Iteration & Community Launch

**Goal:** Incorporate test feedback, release complete build package, establish community.

### 5A — Design Revisions

- [ ] Address all issues identified during testing
- [ ] Optimize layer thicknesses based on simulation + physical data
- [ ] Refine skeleton articulation based on extended wear feedback
- [ ] Finalize bearing rail design for reliability

### 5B — Documentation Package

- [ ] Step-by-step construction guide with photos
- [ ] Video tutorials for critical techniques (quilting, HDPE forming, bearing assembly)
- [ ] Printable pattern files for all sizes (DXF, SVG, PDF tiled)
- [ ] Complete BOM with verified supplier links and pricing
- [ ] Build log template for community members

### 5C — Community Tools

- [ ] Web-based size calculator (measurements → recommended size + pattern)
- [ ] Materials cost estimator (configuration → itemized BOM + total cost)
- [ ] Supplier database with regional alternatives
- [ ] Standardized test result submission format

### 5D — Standards & Specifications

- [ ] Publish helmet rail profile specification (cross-section, curvature, mounting interface)
- [ ] Publish attachment zone specification (MOLLE spacing, hardpoint threading, load ratings)
- [ ] Publish size grading standard (body measurements → pattern dimensions)

**Deliverables:** Complete open-source build package, community infrastructure, published standards

---

## Phase 6: Advanced Development (Long-Term)

### 6A — Simulation Enhancements

- [ ] Composite laminate analysis via Code_Aster (per-ply stress extraction)
- [ ] CFD ventilation analysis via OpenFOAM (`chtMultiRegionFoam` for air gaps)
- [ ] Multi-physics coupling via preCICE (CalculiX + OpenFOAM thermal-structural-fluid)
- [ ] Fatigue analysis for skeleton components under cyclic loading

### 6B — Design Variants

- [ ] Hot-climate variant (maximized ventilation, reduced batting, mesh panels)
- [ ] Cold-climate variant (increased insulation, integrated heating channels)
- [ ] Activity-specific variants (climbing, cycling, mounted)
- [ ] Modular sleeve system (detachable, activity-matched)

### 6C — Manufacturing Scaling

- [ ] Small-batch production tooling designs (cutting templates, forming jigs, assembly fixtures)
- [ ] Quality control checklist and inspection fixtures
- [ ] Cost optimization for 25+ unit production runs

### 6D — Technology Integration

- [ ] Strain gauge sensor integration for load monitoring
- [ ] Temperature sensor array for thermal mapping
- [ ] Modular heating element pockets (USB-powered, cold weather)
- [ ] Phase change material (PCM) cooling pocket integration

---

## Milestone Summary

| Phase | Focus | Key Output |
|-------|-------|------------|
| **0** | Foundation | Dev environment, governance, config schema |
| **1** | Materials + Geometry | Parametric STEP assemblies, material library |
| **2** | Simulation | Static, thermal, and impact FEA workflows |
| **3** | Patterns + Prototype | Physical build, sewing patterns, fabrication drawings |
| **4** | Testing | Test data, simulation validation, design feedback |
| **5** | Community Launch | Build package, community tools, published standards |
| **6** | Advanced | Multi-physics, variants, manufacturing scaling |

---

## Contributing

See the whitepaper §11 for contribution areas. All design changes require comparative testing data. Major changes go through peer review by multiple builders. Follow documentation standards for consistent formatting and photography.
