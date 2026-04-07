"""Molecular descriptor calculations."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional RDKit import
# ---------------------------------------------------------------------------
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit.Chem.rdMolDescriptors import CalcTPSA
    _RDKIT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RDKIT_AVAILABLE = False
    logger.warning("rdkit_not_available", msg="Molecular descriptor calculations will be limited.")


class MolecularDescriptors:
    """Compute 2-D molecular descriptors from RDKit Mol objects."""

    @staticmethod
    def compute_2d_descriptors(mol: Any) -> Dict[str, float]:
        """
        Compute core 2-D descriptors for a molecule.

        Args:
            mol: RDKit Mol object.

        Returns:
            Dictionary of descriptor name → value.
        """
        if not _RDKIT_AVAILABLE or mol is None:
            return {}
        return {
            "molecular_weight": round(Descriptors.ExactMolWt(mol), 4),
            "logp": round(Descriptors.MolLogP(mol), 4),
            "hbd": rdMolDescriptors.CalcNumHBD(mol),
            "hba": rdMolDescriptors.CalcNumHBA(mol),
            "tpsa": round(CalcTPSA(mol), 4),
            "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
            "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "heavy_atoms": mol.GetNumHeavyAtoms(),
            "rings": rdMolDescriptors.CalcNumRings(mol),
            "stereo_centers": len(
                Chem.FindMolChiralCenters(mol, includeUnassigned=True)
            ),
            "fraction_csp3": round(rdMolDescriptors.CalcFractionCSP3(mol), 4),
        }

    @staticmethod
    def compute_lipinski(mol: Any) -> Dict[str, Any]:
        """
        Evaluate Lipinski's Rule of Five.

        A drug-like molecule should satisfy ≥ 3 of these rules:
        - MW ≤ 500
        - logP ≤ 5
        - HBD ≤ 5
        - HBA ≤ 10
        """
        if not _RDKIT_AVAILABLE or mol is None:
            return {"lipinski_pass": None, "violations": [], "rules": {}}

        mw = Descriptors.ExactMolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)

        rules = {
            "mw_le_500": mw <= 500,
            "logp_le_5": logp <= 5,
            "hbd_le_5": hbd <= 5,
            "hba_le_10": hba <= 10,
        }
        violations = [rule for rule, passed in rules.items() if not passed]

        return {
            "lipinski_pass": len(violations) <= 1,
            "violations": violations,
            "rules": rules,
            "values": {"mw": round(mw, 2), "logp": round(logp, 2), "hbd": hbd, "hba": hba},
        }

    @staticmethod
    def compute_veber(mol: Any) -> Dict[str, Any]:
        """
        Evaluate Veber's rules for oral bioavailability.

        Rules: rotatable bonds ≤ 10 AND TPSA ≤ 140.
        """
        if not _RDKIT_AVAILABLE or mol is None:
            return {"veber_pass": None}

        rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        tpsa = CalcTPSA(mol)

        return {
            "veber_pass": rot_bonds <= 10 and tpsa <= 140,
            "rotatable_bonds": rot_bonds,
            "tpsa": round(tpsa, 2),
        }

    @staticmethod
    def compute_complexity(mol: Any) -> Dict[str, float]:
        """Compute molecular complexity metrics."""
        if not _RDKIT_AVAILABLE or mol is None:
            return {}
        return {
            "bertz_complexity": round(Descriptors.BertzCT(mol), 2),
            "balaban_j": round(Descriptors.BalabanJ(mol), 4) if mol.GetNumBonds() > 0 else 0.0,
        }


def compute_all_descriptors(mol: Any) -> Dict[str, Any]:
    """
    Convenience function: compute all descriptor categories for an RDKit mol.

    Returns merged dictionary of all descriptors plus drug-likeness flags.
    """
    desc = MolecularDescriptors()
    result: Dict[str, Any] = {}
    result.update(desc.compute_2d_descriptors(mol))
    result["lipinski"] = desc.compute_lipinski(mol)
    result["veber"] = desc.compute_veber(mol)
    result["complexity"] = desc.compute_complexity(mol)
    return result
