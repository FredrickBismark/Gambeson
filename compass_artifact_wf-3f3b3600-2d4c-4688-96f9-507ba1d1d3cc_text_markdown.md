# Building a parametric armor simulation pipeline with open-source CAD and FEA tools

A fully open-source, locally-hosted pipeline for generating and simulating a multi-layer quilted armor system is achievable today using FreeCAD (or CadQuery) for parametric modeling, CalculiX and Elmer for FEA, and OpenRadioss for impact simulation. The critical insight is that **no single tool covers the full stack** — the project requires an orchestrated pipeline of 5–7 specialized tools, connected via Python, with geometry flowing as STEP files and results flowing as VTK. This report provides the complete technical blueprint: API patterns, material data, solver configurations, and a production-ready project architecture for Claude Code.

---

## A. FreeCAD Python API powers fully scripted parametric modeling

FreeCAD's Python API wraps the OpenCASCADE (OCCT) kernel and exposes every CAD operation programmatically. The two core modules are `FreeCAD` (aliased `App`) for document/object management and `Part` for solid modeling. Every GUI operation has a Python equivalent, discoverable by enabling "Show script commands in Python console" in preferences.

**Core geometry creation** follows a topological hierarchy: Vertex → Edge → Wire → Face → Shell → Solid → Compound. The `Part` module provides `makeBox()`, `makeCylinder()`, `makeSphere()`, `makeShell()`, `makeSolid()`, and `makeCompound()`. Boolean operations use `shape.fuse()`, `shape.cut()`, and `shape.common()`. Extrusion, loft, sweep, and revolve are all scriptable — `face.extrude(vector)`, `Part.makeLoft([wires])`, and `Wire.makePipeShell([profiles])`.

For the 6-layer armor material stack, the recommended approach uses **`makeOffsetShape()`** to create concentric shells from a base body form:

```python
layers = [("SpacerMesh", 3.0), ("CottonBatting", 6.0), ("HDPE_Skeleton", 4.0),
          ("EVA_D3O_Foam", 8.0), ("QuiltedBatting", 5.0), ("CORDURA_Shell", 1.5)]
cumulative = 0.0
for name, thickness in layers:
    cumulative += thickness
    outer = base_shape.makeOffsetShape(cumulative, 0.01)
    inner = base_shape.makeOffsetShape(cumulative - thickness, 0.01)
    layer_solid = outer.cut(inner)
```

This wraps OCCT's `BRepOffsetAPI_MakeOffsetShape` and can fail on sharp features — use tolerance values of 0.01–0.1 and avoid degenerate geometry. For flat panel sections, sequential extrusion with `face.extrude()` is more reliable.

**Assembly modeling** in FreeCAD 1.0 (released November 2024) uses the new built-in Assembly workbench based on the Ondsel Solver. For scripted assemblies, **Assembly4** remains more suitable because it uses deterministic `ExpressionEngine` placement via Local Coordinate Systems rather than iterative constraint solving. Objects link via `App::Link`, and placement is set through expressions: `link.setExpression('Placement', 'LCS_Origin.Placement * Part.LCS_Attach.Placement ^ -1')`. For simpler multi-body models without constraints, creating multiple `Part::Feature` objects in a single document and grouping them via `Part::Compound` is sufficient.

**Material assignment** for FEM requires creating `Fem::MaterialSolid` objects via `ObjectsFem.makeMaterialSolid()` and assigning them to specific solids through `References`. The critical prerequisite is using **`Part::BooleanFragments` in CompSolid mode** — this creates shared mesh interfaces between adjacent bodies, which is mandatory for conforming multi-material FEM meshes.

**CadQuery** (`github.com/CadQuery/cadquery`, **4,500+ stars**) deserves serious consideration as an alternative geometry kernel. It uses OCCT directly, is pip-installable, runs headless natively, and exports STEP files without FreeCAD. For purely programmatic geometry generation feeding into a FEA pipeline, CadQuery's fluent API is more ergonomic than raw FreeCAD scripting.

Key documentation: `wiki.freecad.org/Topological_data_scripting`, `wiki.freecad.org/FEM_Tutorial_Python`, `freecad-python-stubs.readthedocs.io` for IDE completion.

---

## B. FreeCAD FEM handles static and thermal analysis well but not ballistic impact

The FEM workbench supports **static structural, frequency/modal, buckling, and thermo-mechanical analysis** through CalculiX, plus **thermal, electromagnetic, and flow analysis** through Elmer. FreeCAD 1.0 brought significant FEM improvements including new constraint types, PaStiX/Pardiso solvers, and material system rework.

**CalculiX integration** is the backbone for structural work. The solver is configured via `ObjectsFem.makeSolverCalculixCcxTools()` with properties for analysis type, geometric nonlinearity, material nonlinearity, and matrix solver. The full FEM workflow is scriptable:

```python
from femtools import ccxtools
fea = ccxtools.FemToolsCcx()
fea.update_objects(); fea.setup_working_dir(); fea.setup_ccx()
if not fea.check_prerequisites():
    fea.write_inp_file(); fea.ccx_run(); fea.load_results()
```

**Multi-material setup** follows a strict pattern: create separate solid bodies → combine with `Part::BooleanFragments` (CompSolid mode) → create `Fem::MaterialSolid` per material → assign each to its sub-solid via `References = [(bf_object, "Solid1")]`. The FEM examples at `src/Mod/Fem/femexamples/` include `material_multiple_bendingbeam_fiveboxes` demonstrating this exact workflow.

**Load case definition** uses `ObjectsFem.makeConstraintForce()`, `makeConstraintPressure()`, `makeConstraintFixed()`, `makeConstraintDisplacement()`, `makeConstraintTemperature()`, `makeConstraintHeatflux()`, and `makeConstraintSelfWeight()`. For the shoulder yoke load case (15–30 kg), apply **300 N** as a force constraint on the yoke contact faces. FreeCAD uses the mm/N/s unit system internally, so forces are in millinewtons in some API calls — verify units carefully.

**Thermal simulation** through the layered composite is feasible two ways. CalculiX's `thermomech` analysis type handles coupled thermo-mechanical problems with temperature BCs on the body-side surface (310.15 K) and convective heat flux on the outer surface (film coefficient ~5–25 W/m²K, ambient 293 K). Each layer gets distinct thermal conductivity through its material assignment. **Elmer is preferred for pure thermal analysis** — it supports steady-state and transient heat equation solving with better control over timestepping and decoupled thermal-only solutions.

**Meshing** uses Gmsh (recommended) or Netgen. For thin layers, either use **solid elements with ≥2–3 elements through thickness** (expensive) or **shell elements via `ElementGeometry2D`** (efficient, define thickness as a property). Mesh refinement at critical zones uses `ObjectsFem.makeMeshRegion()`. **Second-order elements (C3D10, 10-node tetrahedra) are significantly more accurate** and should always be used.

**Impact simulation is the major limitation.** CalculiX supports implicit dynamics (`*DYNAMIC` keyword) suitable for quasi-static or slow-impact events, but this requires manual `.inp` file editing — FreeCAD's GUI doesn't expose dynamic analysis. CalculiX's explicit dynamics mode (`*DYNAMIC,EXPLICIT`) exists but is **unreliable for complex problems**: contact with plasticity fails, shell elements have convergence issues, and community reports frequent segfaults. For true impact/ballistic analysis, export the mesh and use an external explicit solver.

What FreeCAD FEM **cannot do**: high-velocity impact simulation, native composite laminate theory (ply failure), coupled fluid-thermal CFD, or hex-dominant meshing for layered structures.

---

## C. OpenSCAD excels at parametric mechanical components via BOSL2

OpenSCAD's code-first CSG approach is ideal for the ball bearing rail track, HDPE skeleton plates, and articulated spine segments. The **200mm arc V-groove rail** is modeled by defining a V-groove `polygon()` cross-section, translating it to the desired radius, then applying `rotate_extrude(angle=X)` where the radius is calculated from `r = 200/angle_in_radians`.

**BOSL2** (`github.com/BelfrySCAD/BOSL2`, **2,000+ stars**, BSD-2, actively maintained) is the essential library. It provides `path_sweep()` for sweeping profiles along arbitrary curves (critical for the curved rail), an attachments system for positioning parts without manual coordinate math, involute gear generation, threading, bezier curves, and robust rounding/filleting. For the V-groove rail specifically, define the V-groove profile as a 2D path and sweep it along a circular arc using BOSL2's `path_sweep()`.

**NopSCADlib** (`github.com/nophead/NopSCADlib`, GPLv3) provides a massive vitamin library including **ball bearings, linear bearings, rod ends (spherical bearings), linear rails, and fasteners** — directly applicable to the rail interface. It also generates BOMs and assembly documentation automatically.

**Size grading (S through XXL)** uses OpenSCAD's Customizer feature with lookup tables:

```openscad
sizes = [["S",420,340],["M",440,360],["L",460,380],["XL",480,400],["XXL",500,420]];
size_index = 2; // Select "L"
chest = sizes[size_index][1];
module armor_plate(chest, waist, shoulder) { /* parametric geometry */ }
```

**The critical interoperability limitation**: OpenSCAD cannot export STEP files natively (GitHub issue #893, open since 2013). The workflow is OpenSCAD → CSG export → FreeCAD CSG import → STEP export. FreeCAD's OpenSCAD workbench handles this import, though `hull()` and `minkowski()` operations are not supported. A conversion script pattern: `importCSG.open("model.csg")` → `Part.export(doc.Objects, "model.step")`. For STL-only exports, FreeCAD can convert via Part → Create shape from mesh → Sew → Refine → Export STEP, but this produces tessellated geometry.

**SolidPython2** (`pip install solidpython2`, v2.1.3, LGPL-2.1) is the recommended Python interface. It maps Python operators to OpenSCAD operations (`+` = union, `-` = difference, `*` = intersection) and has built-in BOSL2 support. **PythonSCAD** is an emerging alternative where Python runs natively inside OpenSCAD itself — the OpenSCAD core team began merging this in February 2025.

---

## D. OpenRadioss fills the critical impact simulation gap

The open-source FEA ecosystem beyond FreeCAD fills specific capability gaps, with **OpenRadioss as the standout tool for impact simulation**.

**OpenRadioss** (`github.com/OpenRadioss/OpenRadioss`, AGPL-3.0) is the former commercial Altair Radioss, open-sourced in September 2022. It is **the most complete open-source explicit dynamics solver available**, industry-proven for 30+ years in automotive crash simulation (5-star NCAP-rated vehicles were designed with it). Key capabilities include composite and sandwich shell elements, nonlinear material models with damage, LS-DYNA input format compatibility, and hybrid SMP+MPI parallelization. A fully open-source crash workflow was demonstrated at the 2025 Carhs aCAE Grand Challenge: FreeCAD → PrePoMax → OpenRadioss → ParaView.

**PrePoMax** (`prepomax.fs.um.si`, v2.5.0 February 2026) is the recommended FEA pre/post-processor for CalculiX. It provides a modern GUI that dramatically lowers the learning curve compared to command-line CCX, supports STEP/IGES import, integrated Netgen meshing, and recently added OpenRadioss export. **For this project, the optimal workflow is FreeCAD for CAD → STEP export → PrePoMax for FEA setup → CalculiX/OpenRadioss solving → ParaView visualization.**

**Salome-Meca / Code_Aster** (developed by EDF for nuclear safety, GPL) provides capabilities beyond CalculiX: fatigue analysis, fracture mechanics, **composite shell elements with arbitrary layer definitions and per-layer stress extraction**, and advanced contact algorithms. Code_Aster's composite shell capability directly maps to the multi-layer armor use case. The tradeoff is a steeper learning curve and primarily Linux support.

**Elmer FEM** (`github.com/ElmerCSC/elmerfem`, GPLv2, developed by CSC Finland) is the best choice for thermal multiphysics — it supports anisotropic conduction, temperature-dependent properties, phase change, and scales to thousands of cores via MPI. For the armor thermal comfort analysis, Elmer handles the body heat → layers → ambient heat path with coupled thermal-structural effects.

**OpenFOAM** adds CFD capability for ventilation analysis. Its `chtMultiRegionFoam` solver handles conjugate heat transfer between solid armor layers and fluid air gaps. The `turbulentTemperatureCoupledBaffleMixed` boundary condition supports specifying multi-layer thermal resistance without meshing thin layers. This is directly applicable to modeling air gaps between armor and body.

**preCICE** (`precice.org`) is the coupling framework that connects these solvers — it can run CalculiX + OpenFOAM partitioned simulations for fluid-structure-thermal interaction.

| Simulation task | Recommended solver | Alternative |
|---|---|---|
| Static structural (weight, compression) | CalculiX via FreeCAD FEM | Code_Aster |
| Thermal through layers | Elmer FEM | CalculiX thermomech |
| High-speed impact | **OpenRadioss** | None open-source at this level |
| Ventilation/airflow CFD | OpenFOAM | — |
| Composite laminate stress | Code_Aster | CalculiX composite shells |
| Multi-physics coupling | preCICE | Elmer built-in |

---

## E. The project architecture should be config-driven with isolated solver modules

The recommended architecture uses a **configuration-driven Python pipeline** where YAML files define geometry parameters, material properties, and simulation settings. Each module (geometry, simulation, post-processing) operates independently and communicates through files (STEP, INP, VTK).

```
armor-sim/
├── CLAUDE.md                      # Project context for Claude Code
├── config/
│   ├── armor_config.yaml          # Parametric dimensions, size grading
│   ├── materials.yaml             # Material property database
│   └── simulation_params.yaml     # Solver settings, load cases
├── src/
│   ├── geometry/                  # CAD generation (CadQuery or FreeCAD)
│   ├── simulation/                # FEA setup (CalculiX, Elmer runners)
│   ├── postprocessing/            # Results → VTK → PyVista images
│   └── pipeline/orchestrator.py   # End-to-end workflow controller
├── docker/Dockerfile              # Headless environment
└── output/                        # Generated STEP, meshes, results
```

**FreeCAD headless mode** runs via `FreeCADCmd` (no GUI dependencies) or by importing FreeCAD as a Python module with `sys.path.append('/usr/lib/freecad/lib/')`. The Docker image `amrit3701/freecad-cli` provides FreeCAD compiled without GUI. The official `FreeCAD/FC-Worker` repository offers a containerized headless runner pattern.

**The pipeline flow** is: Parameters (YAML) → CadQuery/SolidPython2 generates geometry → OpenSCAD CLI renders mechanical parts to STL → FreeCAD assembles and converts to STEP → Gmsh meshes the assembly → CalculiX/Elmer solve → meshio converts results → PyVista renders visualizations. Each step is a Python function callable independently.

**Key Python packages** form the pipeline backbone:

- **CadQuery** (`pip install cadquery`) — geometry generation with native STEP export, arguably the best choice since it eliminates the OpenSCAD → FreeCAD conversion step
- **SolidPython2** (`pip install solidpython2`) — Python→OpenSCAD for mechanical components
- **PyCCX** (`pip install PyCCX`) — full CalculiX pipeline: geometry → Gmsh mesh → .inp → solve → VTK
- **pygccx** (`github.com/calculix/pygccx`) — official CalculiX Python framework
- **pyelmer** (`pip install pyelmer`) — object-oriented Elmer setup generating .sif files
- **meshio** (`pip install meshio`) — universal mesh I/O supporting 40+ formats including Abaqus .inp, Gmsh .msh, VTK/VTU
- **PyVista** (`pip install pyvista`) — 3D visualization with headless rendering via `Plotter(off_screen=True)`

**Solver integration** uses subprocess calls. CalculiX runs as `ccx -i input_file` (reads `input_file.inp`, produces `.frd` results). Elmer runs as `ElmerSolver case.sif`. OpenRadioss has its own CLI. All solvers read text-based input files and produce standard output formats convertible to VTK via meshio.

For **Claude Code specifically**, the CLAUDE.md should document the tech stack, key commands, code style conventions, and architecture rules. Keep files under ~300 lines, use type hints everywhere, and isolate FreeCAD imports to a single setup module. Subdirectory CLAUDE.md files provide domain-specific context.

---

## F. Material properties for all seven layers with CalculiX card syntax

Compiling reliable material data for the armor stack reveals that **HDPE and nylon have well-documented properties, while foams and proprietary materials like D3O require approximation**. All values below use the CalculiX unit system (mm, N, s, K) where density is in tonnes/mm³ and conductivity in mW/(mm·K).

| Material | Density (kg/m³) | Young's Modulus | Poisson's Ratio | Thermal Conductivity (W/m·K) | FEA Model |
|---|---|---|---|---|---|
| **HDPE** (6mm skeleton) | 950 | 1100 MPa | 0.42 | 0.46 | Linear elastic |
| **EVA foam** (85 kg/m³) | 85 | ~2.5 MPa compressive | ~0.05 | 0.04 | *HYPERFOAM N=1 |
| **D3O** (viscoelastic) | 200–500 | 0.5–100 MPa (rate-dependent) | ~0.05 | 0.04–0.07 | *HYPERFOAM + *VISCOELASTIC |
| **Cotton batting** | 40–80 | ~0.01 MPa | 0.1 | 0.038 | Very soft elastic or omit structural |
| **CORDURA 1000D** | 1140 (solid nylon) | 2.8 GPa (warp/fill) | 0.35 | 0.25 | *ELASTIC TYPE=ORTHO (shell) |
| **Closed-cell foam** | 30–100 | 0.5–20 MPa | 0.0–0.3 | 0.03–0.06 | *HYPERFOAM |
| **3D spacer mesh** | ~134 | ~5 MPa effective | 0.2 | 0.06 | Homogenized elastic |

**FreeCAD material cards** use the `.FCMat` INI format with properties like `YoungsModulus = 1100 MPa`, `Density = 950 kg/m^3`, and `ThermalConductivity = 0.46 W/m/K`. Custom cards go in `~/.FreeCAD/Material/`. The Python API reads them via `importFCMat.read("path.FCMat")`.

**CalculiX material definitions** require careful unit conversion. A complete multi-material `.inp` block for the armor stack:

```
*MATERIAL, NAME=HDPE
*ELASTIC
1100., 0.42
*DENSITY
9.5e-7
*CONDUCTIVITY
0.46
*SPECIFIC HEAT
2.1e9

*MATERIAL, NAME=EVA_FOAM
*HYPERFOAM, N=1
1.25, 2.0, 0.0
*DENSITY
8.5e-8
*CONDUCTIVITY
0.04

*MATERIAL, NAME=CORDURA_1000D
*ELASTIC, TYPE=ENGINEERING CONSTANTS
2800., 2800., 200., 0.35, 0.1, 0.1, 500., 100.
100.
*DENSITY
3.15e-7
```

**EVA foam** should use `*HYPERFOAM` (Ogden-type compressible foam model) rather than linear elastic. Parameters μ₁ ≈ 1.25 MPa and α₁ ≈ 2.0 capture the three-stage compression behavior (linear → plateau → densification). For **D3O's rate-dependent behavior**, combine `*HYPERFOAM` with `*VISCOELASTIC` using Prony series relaxation terms — this captures the characteristic softness-to-stiffness switching. Since D3O properties are proprietary, approximate with published polyurethane foam data at similar density.

**CORDURA** requires orthotropic shell modeling with `*ELASTIC, TYPE=ENGINEERING CONSTANTS` specifying warp and fill moduli (~2.8 GPa each for nylon 6,6 fabric), through-thickness modulus (~0.2 GPa, much softer), and in-plane shear modulus (~0.5 GPa). **Cotton batting** is so compliant (E ~0.01 MPa) that it can be omitted from structural analysis and included only in thermal models.

Key material databases: MatWeb (`matweb.com`, broad coverage, partially free), MakeItFrom (`makeitfrom.com`, free), DesignerData (`designerdata.nl`, plastics focus). The critical data gap is **foam and textile FEA properties** — no free database provides ready-to-use FEA data for these materials. Literature review through MDPI and ScienceDirect is necessary, particularly the MDPI Polymers 2024 study on EVA foam compression at various densities.

---

## Conclusion: a viable but multi-tool pipeline with one critical decision point

The entire pipeline is buildable with open-source, self-hosted tools. The **architecture decision with the highest impact** is whether to use CadQuery (cleaner Python API, native STEP, pip-installable) or FreeCAD's Part module (more mature assembly support, integrated FEM) for geometry generation — CadQuery for geometry feeding into PrePoMax/CalculiX is likely the most productive path, with FreeCAD reserved for assembly and FEM-integrated workflows.

The three simulation tiers map cleanly to available solvers: **CalculiX for static structural** (shoulder loads, compression, buckling of HDPE plates), **Elmer for steady-state and transient thermal** (body heat through the 6-layer stack), and **OpenRadioss for impact/dynamic analysis** (the only credible open-source explicit dynamics solver). PrePoMax bridges the gap between CAD geometry and solver input with a modern GUI when manual intervention is needed.

The material modeling challenge is real but manageable. Linear elastic models suffice for HDPE and CORDURA under normal loads. EVA foam requires hyperfoam constitutive models, and D3O requires viscoelastic extensions — both supported by CalculiX but requiring manual `.inp` editing beyond FreeCAD's GUI capabilities. Building a library of validated `.inp` material blocks and `.FCMat` cards early in the project will pay dividends across every simulation run.