"""Unit tests for the chemoinformatics service and molecular descriptors."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# RDKit availability flag — all tests must pass whether or not RDKit is
# installed.  We check once at module import time and skip RDKit-only tests
# when it is absent.
# ---------------------------------------------------------------------------

try:
    from rdkit import Chem  # noqa: F401
    _RDKIT_AVAILABLE = True
except ImportError:
    _RDKIT_AVAILABLE = False

rdkit_required = pytest.mark.skipif(
    not _RDKIT_AVAILABLE,
    reason="RDKit is not installed in this environment",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"


def _mol(smiles: str) -> Any:
    """Return an RDKit Mol object, or None if RDKit unavailable."""
    if not _RDKIT_AVAILABLE:
        return None
    from rdkit import Chem
    return Chem.MolFromSmiles(smiles)


# ---------------------------------------------------------------------------
# SMILES validation
# ---------------------------------------------------------------------------


def test_validate_smiles_valid_aspirin():
    """Aspirin SMILES is valid and parseable."""
    if not _RDKIT_AVAILABLE:
        pytest.skip("RDKit not available")
    from rdkit import Chem

    mol = Chem.MolFromSmiles(ASPIRIN_SMILES)
    assert mol is not None


def test_validate_smiles_invalid():
    """Completely invalid SMILES returns None from RDKit."""
    if not _RDKIT_AVAILABLE:
        pytest.skip("RDKit not available")
    from rdkit import Chem

    mol = Chem.MolFromSmiles("INVALID_SMILES_XYZ_123")
    assert mol is None


def test_validate_smiles_empty():
    """Empty SMILES returns None from RDKit."""
    if not _RDKIT_AVAILABLE:
        pytest.skip("RDKit not available")
    from rdkit import Chem

    mol = Chem.MolFromSmiles("")
    assert mol is None


# ---------------------------------------------------------------------------
# MolecularDescriptors — compute_2d_descriptors
# ---------------------------------------------------------------------------


@rdkit_required
def test_compute_descriptors_aspirin():
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    mol = _mol(ASPIRIN_SMILES)
    desc = MolecularDescriptors()
    result = desc.compute_2d_descriptors(mol)

    assert isinstance(result, dict)
    assert "molecular_weight" in result
    assert "logp" in result
    assert "hbd" in result
    assert "hba" in result
    assert "tpsa" in result
    # Aspirin MW is ~180 Da
    assert 170.0 <= result["molecular_weight"] <= 185.0


@rdkit_required
def test_compute_descriptors_returns_empty_for_none():
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    desc = MolecularDescriptors()
    result = desc.compute_2d_descriptors(None)
    assert result == {}


# ---------------------------------------------------------------------------
# Lipinski Rule of Five — Aspirin
# ---------------------------------------------------------------------------


@rdkit_required
def test_lipinski_rule_of_five_aspirin():
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    mol = _mol(ASPIRIN_SMILES)
    desc = MolecularDescriptors()
    result = desc.compute_lipinski(mol)

    assert isinstance(result, dict)
    assert "lipinski_pass" in result
    assert "violations" in result
    assert "rules" in result
    # Aspirin satisfies all Lipinski rules
    assert result["lipinski_pass"] is True
    assert result["violations"] == []


@rdkit_required
def test_lipinski_rule_of_five_structure():
    """Verify compute_lipinski returns expected keys."""
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    mol = _mol(ASPIRIN_SMILES)
    desc = MolecularDescriptors()
    result = desc.compute_lipinski(mol)

    assert "mw_le_500" in result["rules"]
    assert "logp_le_5" in result["rules"]
    assert "hbd_le_5" in result["rules"]
    assert "hba_le_10" in result["rules"]


def test_lipinski_without_rdkit_returns_none_pass():
    """When RDKit is absent, lipinski_pass must be None (graceful degradation)."""
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    desc = MolecularDescriptors()
    result = desc.compute_lipinski(None)
    assert result["lipinski_pass"] is None


# ---------------------------------------------------------------------------
# Veber rules
# ---------------------------------------------------------------------------


@rdkit_required
def test_veber_rules_aspirin():
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    mol = _mol(ASPIRIN_SMILES)
    desc = MolecularDescriptors()
    result = desc.compute_veber(mol)

    assert "veber_pass" in result
    assert "rotatable_bonds" in result
    assert "tpsa" in result
    assert result["veber_pass"] is True


def test_veber_without_rdkit_returns_none_pass():
    from app.services.chemoinformatics.descriptors import MolecularDescriptors

    desc = MolecularDescriptors()
    result = desc.compute_veber(None)
    assert result["veber_pass"] is None


# ---------------------------------------------------------------------------
# Tanimoto similarity
# ---------------------------------------------------------------------------


@rdkit_required
def test_tanimoto_similarity_identical_molecules():
    """Identical molecules have Tanimoto score of 1.0."""
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator

    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    mol = _mol(ASPIRIN_SMILES)
    fp = gen.GetFingerprint(mol)
    score = DataStructs.TanimotoSimilarity(fp, fp)
    assert score == pytest.approx(1.0)


@rdkit_required
def test_tanimoto_similarity_different_molecules():
    """Different molecules have Tanimoto score strictly less than 1.0."""
    from rdkit import DataStructs
    from rdkit.Chem import rdFingerprintGenerator

    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    mol1 = _mol(ASPIRIN_SMILES)
    mol2 = _mol("CCO")  # Ethanol — very different
    fp1 = gen.GetFingerprint(mol1)
    fp2 = gen.GetFingerprint(mol2)
    score = DataStructs.TanimotoSimilarity(fp1, fp2)
    assert score < 1.0


# ---------------------------------------------------------------------------
# ADMET prediction via ChemoinformaticsService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admet_prediction_aspirin():
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()
    result = await svc.predict_admet(ASPIRIN_SMILES)

    if not _RDKIT_AVAILABLE:
        assert "error" in result
    else:
        assert "absorption" in result
        assert "distribution" in result
        assert "excretion" in result
        assert "toxicity" in result
        assert isinstance(result["toxicity"]["alerts"], list)


@pytest.mark.asyncio
async def test_admet_prediction_returns_dict():
    """predict_admet must always return a dict regardless of RDKit availability."""
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()
    result = await svc.predict_admet(ASPIRIN_SMILES)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# ChemoinformaticsService — analyze_molecule fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_molecule_fallback_when_no_rdkit():
    """When RDKit is not available, the service uses the fallback path."""
    from app.services.chemoinformatics import service as chem_module
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()

    original = chem_module._RDKIT_AVAILABLE
    try:
        chem_module._RDKIT_AVAILABLE = False
        result = await svc.analyze_molecule(ASPIRIN_SMILES)
        assert result["is_valid"] is True
        assert result["smiles"] == ASPIRIN_SMILES
        assert "note" in result
    finally:
        chem_module._RDKIT_AVAILABLE = original


@pytest.mark.asyncio
async def test_analyze_molecule_valid_smiles():
    """analyze_molecule returns a dict with is_valid=True for a valid SMILES."""
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()
    result = await svc.analyze_molecule(ASPIRIN_SMILES)

    assert isinstance(result, dict)
    assert result["is_valid"] is True


# ---------------------------------------------------------------------------
# ChemoinformaticsService — compute_descriptors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compute_descriptors_returns_dict():
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()
    result = await svc.compute_descriptors(ASPIRIN_SMILES)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_compute_descriptors_no_rdkit_returns_error_key():
    """Without RDKit, compute_descriptors should return an error indication."""
    from app.services.chemoinformatics import service as chem_module
    from app.services.chemoinformatics.service import ChemoinformaticsService

    svc = ChemoinformaticsService()
    original = chem_module._RDKIT_AVAILABLE
    try:
        chem_module._RDKIT_AVAILABLE = False
        result = await svc.compute_descriptors(ASPIRIN_SMILES)
        assert "error" in result
    finally:
        chem_module._RDKIT_AVAILABLE = original
