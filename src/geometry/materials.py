"""Material database loader and CalculiX/FCMat generator.

Loads material properties from config/materials.yaml and provides:
- Validated material property access
- CalculiX .inp material block generation
- FreeCAD .FCMat card generation
- Unit conversion helpers (SI → CalculiX mm/N/s/K system)
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Unit conversion constants: SI → CalculiX (mm/N/s/K)
# Density: kg/m³ → tonnes/mm³ (multiply by 1e-9)
DENSITY_SI_TO_CCX = 1e-9
# Specific heat: J/(kg·K) → mJ/(tonne·K) (multiply by 1e6)
# 1 J = 1000 mJ, 1 kg = 1e-3 tonne → factor = 1000 / 1e-3 = 1e6
SPECIFIC_HEAT_SI_TO_CCX = 1e6
# Conductivity and modulus have same numeric value in both systems
# (W/(m·K) = mW/(mm·K), MPa = N/mm²)


@dataclass
class Material:
    """A single material with its properties and FEA model type."""

    name: str
    description: str
    density_si: float  # kg/m³
    model: str  # linear_elastic, hyperfoam, hyperfoam_viscoelastic, orthotropic_shell
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float  # J/(kg·K)
    # Linear elastic
    youngs_modulus: float | None = None  # MPa
    poissons_ratio: float | None = None
    # Hyperfoam (Ogden)
    hyperfoam: dict[str, Any] | None = None
    # Viscoelastic (Prony series)
    viscoelastic: dict[str, Any] | None = None
    # Orthotropic
    orthotropic: dict[str, Any] | None = None
    # Metadata
    notes: str = ""
    sources: list[str] = field(default_factory=list)

    @property
    def density_ccx(self) -> float:
        """Density in CalculiX units (tonnes/mm³)."""
        return self.density_si * DENSITY_SI_TO_CCX

    @property
    def specific_heat_ccx(self) -> float:
        """Specific heat in CalculiX units (mJ/(tonne·K))."""
        return self.specific_heat * SPECIFIC_HEAT_SI_TO_CCX

    def to_inp_block(self) -> str:
        """Generate CalculiX .inp material definition block."""
        lines = [f"*MATERIAL, NAME={self.name.upper()}"]

        if self.model == "linear_elastic":
            if self.youngs_modulus is None or self.poissons_ratio is None:
                raise ValueError(
                    f"{self.name}: linear_elastic requires youngs_modulus and poissons_ratio"
                )
            lines.append("*ELASTIC")
            lines.append(f"{self.youngs_modulus}, {self.poissons_ratio}")
        elif self.model == "hyperfoam":
            if self.hyperfoam is None:
                raise ValueError(f"{self.name}: hyperfoam model requires hyperfoam parameters")
            n = self.hyperfoam["N"]
            lines.append(f"*HYPERFOAM, N={n}")
            params = []
            for i in range(1, n + 1):
                params.extend([
                    str(self.hyperfoam[f"mu{i}"]),
                    str(self.hyperfoam[f"alpha{i}"]),
                    str(self.hyperfoam.get(f"nu{i}", 0.0)),
                ])
            lines.append(", ".join(params))
        elif self.model == "hyperfoam_viscoelastic":
            if self.hyperfoam is None or self.viscoelastic is None:
                raise ValueError(
                    f"{self.name}: hyperfoam_viscoelastic requires hyperfoam and viscoelastic params"
                )
            n = self.hyperfoam["N"]
            lines.append(f"*HYPERFOAM, N={n}")
            params = []
            for i in range(1, n + 1):
                params.extend([
                    str(self.hyperfoam[f"mu{i}"]),
                    str(self.hyperfoam[f"alpha{i}"]),
                    str(self.hyperfoam.get(f"nu{i}", 0.0)),
                ])
            lines.append(", ".join(params))
        elif self.model == "orthotropic_shell":
            if self.orthotropic is None:
                raise ValueError(f"{self.name}: orthotropic_shell requires orthotropic parameters")
            o = self.orthotropic
            lines.append("*ELASTIC, TYPE=ENGINEERING CONSTANTS")
            lines.append(
                f"{o['E1']}, {o['E2']}, {o['E3']}, "
                f"{o['nu12']}, {o['nu13']}, {o['nu23']}, "
                f"{o['G12']}, {o['G13']}"
            )
            lines.append(f"{o['G23']}")

        # Density
        lines.append("*DENSITY")
        lines.append(f"{self.density_ccx:.2e}")

        # Thermal properties
        lines.append("*CONDUCTIVITY")
        lines.append(f"{self.thermal_conductivity}")
        lines.append("*SPECIFIC HEAT")
        lines.append(f"{self.specific_heat_ccx:.2e}")

        # Viscoelastic Prony series (after main block)
        if self.model == "hyperfoam_viscoelastic" and self.viscoelastic:
            lines.append("*VISCOELASTIC")
            g_prony = self.viscoelastic["g_prony"]
            k_prony = self.viscoelastic["k_prony"]
            tau = self.viscoelastic["tau"]
            for g, k, t in zip(g_prony, k_prony, tau):
                lines.append(f"{g}, {k}, {t}")

        return "\n".join(lines)

    def to_fcmat(self) -> str:
        """Generate FreeCAD .FCMat material card content."""
        sections = []

        sections.append("[General]")
        sections.append(f"Name = {self.name}")
        sections.append(f"Description = {self.description}")
        if self.sources:
            sections.append(f"SourceURL = {self.sources[0]}")

        sections.append("")
        sections.append("[Mechanical]")
        sections.append(f"Density = {self.density_si} kg/m^3")
        if self.youngs_modulus is not None:
            sections.append(f"YoungsModulus = {self.youngs_modulus} MPa")
        elif self.orthotropic is not None:
            # Use in-plane average for FreeCAD (isotropic approximation)
            e_avg = (self.orthotropic["E1"] + self.orthotropic["E2"]) / 2
            sections.append(f"YoungsModulus = {e_avg} MPa")
        elif self.hyperfoam is not None:
            # Approximate Young's modulus from hyperfoam mu
            e_approx = 3 * self.hyperfoam["mu1"]
            sections.append(f"YoungsModulus = {e_approx:.1f} MPa")
        if self.poissons_ratio is not None:
            sections.append(f"PoissonRatio = {self.poissons_ratio}")

        sections.append("")
        sections.append("[Thermal]")
        sections.append(f"ThermalConductivity = {self.thermal_conductivity} W/m/K")
        sections.append(f"SpecificHeat = {self.specific_heat} J/kg/K")

        return "\n".join(sections) + "\n"


class MaterialDatabase:
    """Load and query the material property database."""

    def __init__(self, config_path: Path | None = None) -> None:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "materials.yaml"
        self._path = config_path
        self._materials: dict[str, Material] = {}
        self._load()

    def _load(self) -> None:
        with open(self._path) as f:
            data = yaml.safe_load(f)

        for name, props in data["materials"].items():
            self._materials[name] = Material(
                name=name,
                description=props.get("description", ""),
                density_si=props["density_si"],
                model=props["model"],
                thermal_conductivity=props["thermal_conductivity"],
                specific_heat=props["specific_heat"],
                youngs_modulus=props.get("youngs_modulus"),
                poissons_ratio=props.get("poissons_ratio"),
                hyperfoam=props.get("hyperfoam"),
                viscoelastic=props.get("viscoelastic"),
                orthotropic=props.get("orthotropic"),
                notes=props.get("notes", ""),
                sources=props.get("sources", []),
            )

    def get(self, name: str) -> Material:
        """Get a material by name. Raises KeyError if not found."""
        return self._materials[name]

    def all_names(self) -> list[str]:
        """Return all material names."""
        return list(self._materials.keys())

    def generate_inp(self, names: list[str] | None = None) -> str:
        """Generate combined CalculiX .inp material blocks.

        Args:
            names: Material names to include. None = all materials.
        """
        if names is None:
            names = self.all_names()
        header = textwrap.dedent("""\
            ** CalculiX material definitions — Modern Gambeson System
            ** Unit system: mm / N / s / K
            ** Auto-generated from config/materials.yaml
            """)
        blocks = [header]
        for name in names:
            mat = self.get(name)
            blocks.append(f"** {'=' * 60}")
            blocks.append(f"** {mat.description}")
            blocks.append(f"** {'=' * 60}")
            blocks.append(mat.to_inp_block())
            blocks.append("")
        return "\n".join(blocks)

    def generate_fcmat_files(self, output_dir: Path) -> list[Path]:
        """Write .FCMat files for all materials to output_dir."""
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for name, mat in self._materials.items():
            path = output_dir / f"{name}.FCMat"
            path.write_text(mat.to_fcmat())
            paths.append(path)
        return paths

    def validate(self) -> list[str]:
        """Check material properties for common errors. Returns list of warnings."""
        warnings = []
        for name, mat in self._materials.items():
            if mat.density_si <= 0:
                warnings.append(f"{name}: density must be positive")
            if mat.thermal_conductivity <= 0:
                warnings.append(f"{name}: thermal conductivity must be positive")
            if mat.specific_heat <= 0:
                warnings.append(f"{name}: specific heat must be positive")
            if mat.model == "linear_elastic":
                if mat.youngs_modulus is None or mat.youngs_modulus <= 0:
                    warnings.append(f"{name}: linear_elastic requires positive Young's modulus")
                if mat.poissons_ratio is None:
                    warnings.append(f"{name}: linear_elastic requires Poisson's ratio")
                elif not -1 < mat.poissons_ratio < 0.5:
                    warnings.append(f"{name}: Poisson's ratio should be in (-1, 0.5)")
            if mat.model == "hyperfoam" and mat.hyperfoam is None:
                warnings.append(f"{name}: hyperfoam model requires hyperfoam parameters")
            if mat.model == "hyperfoam_viscoelastic":
                if mat.hyperfoam is None:
                    warnings.append(f"{name}: requires hyperfoam parameters")
                if mat.viscoelastic is None:
                    warnings.append(f"{name}: requires viscoelastic parameters")
            if mat.model == "orthotropic_shell" and mat.orthotropic is None:
                warnings.append(f"{name}: orthotropic_shell requires orthotropic parameters")
        return warnings
