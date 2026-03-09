"""Tests for the material database and code generation."""

from __future__ import annotations

from pathlib import Path

from src.geometry.materials import MaterialDatabase


MATERIALS_YAML = Path(__file__).parent.parent / "config" / "materials.yaml"


def test_load_all_materials() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    names = db.all_names()
    assert len(names) >= 7
    assert "HDPE" in names
    assert "EVA_HD" in names
    assert "D3O" in names
    assert "cotton_batting" in names
    assert "CORDURA_500D" in names
    assert "spacer_mesh_3d" in names
    assert "aluminum_6061" in names


def test_hdpe_properties() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    hdpe = db.get("HDPE")
    assert hdpe.density_si == 950
    assert hdpe.youngs_modulus == 1100.0
    assert hdpe.poissons_ratio == 0.42
    assert hdpe.model == "linear_elastic"
    # Check unit conversion
    assert abs(hdpe.density_ccx - 9.5e-7) < 1e-10


def test_eva_hyperfoam() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    eva = db.get("EVA_HD")
    assert eva.model == "hyperfoam"
    assert eva.hyperfoam is not None
    assert eva.hyperfoam["N"] == 1
    assert eva.hyperfoam["mu1"] == 1.25


def test_d3o_viscoelastic() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    d3o = db.get("D3O")
    assert d3o.model == "hyperfoam_viscoelastic"
    assert d3o.hyperfoam is not None
    assert d3o.viscoelastic is not None
    assert len(d3o.viscoelastic["tau"]) == 2


def test_cordura_orthotropic() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    cord = db.get("CORDURA_500D")
    assert cord.model == "orthotropic_shell"
    assert cord.orthotropic is not None
    assert cord.orthotropic["E1"] == 2800.0
    assert cord.orthotropic["G12"] == 500.0


def test_validate_no_errors() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    warnings = db.validate()
    assert len(warnings) == 0, f"Unexpected validation warnings: {warnings}"


def test_generate_inp_block() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    hdpe = db.get("HDPE")
    inp = hdpe.to_inp_block()
    assert "*MATERIAL, NAME=HDPE" in inp
    assert "*ELASTIC" in inp
    assert "1100." in inp
    assert "*DENSITY" in inp
    assert "9.5" in inp.lower() or "9.50" in inp


def test_generate_inp_hyperfoam() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    eva = db.get("EVA_HD")
    inp = eva.to_inp_block()
    assert "*HYPERFOAM, N=1" in inp
    assert "1.25" in inp


def test_generate_inp_viscoelastic() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    d3o = db.get("D3O")
    inp = d3o.to_inp_block()
    assert "*HYPERFOAM" in inp
    assert "*VISCOELASTIC" in inp
    assert "0.001" in inp


def test_generate_inp_orthotropic() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    cord = db.get("CORDURA_500D")
    inp = cord.to_inp_block()
    assert "ENGINEERING CONSTANTS" in inp
    assert "2800." in inp


def test_generate_combined_inp() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    combined = db.generate_inp()
    assert "*MATERIAL, NAME=HDPE" in combined
    assert "*MATERIAL, NAME=EVA_FOAM" in combined.upper() or "*MATERIAL, NAME=EVA_HD" in combined
    assert "*MATERIAL, NAME=D3O" in combined


def test_generate_fcmat() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    hdpe = db.get("HDPE")
    fcmat = hdpe.to_fcmat()
    assert "[General]" in fcmat
    assert "[Mechanical]" in fcmat
    assert "[Thermal]" in fcmat
    assert "950" in fcmat
    assert "1100" in fcmat


def test_specific_heat_conversion() -> None:
    db = MaterialDatabase(MATERIALS_YAML)
    hdpe = db.get("HDPE")
    # J/(kg·K) → mJ/(tonne·K): multiply by 1e6
    # 2100 J/(kg·K) = 2100 × 1e6 mJ/(tonne·K) = 2.1e9
    assert hdpe.specific_heat == 2100.0
    assert hdpe.specific_heat_ccx == 2.1e9
