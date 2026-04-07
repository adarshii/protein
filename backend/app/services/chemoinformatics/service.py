"""Chemoinformatics service — core business logic."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exception_handlers import ExternalAPIError, MoleculeValidationError
from app.services.chemoinformatics.descriptors import (
    MolecularDescriptors,
    compute_all_descriptors,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional RDKit import
# ---------------------------------------------------------------------------
try:
    from rdkit import Chem, DataStructs
    from rdkit.Chem import AllChem, MACCSkeys, rdFingerprintGenerator
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    _RDKIT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RDKIT_AVAILABLE = False
    logger.warning("rdkit_not_available", msg="ChemoinformaticsService will use fallback mode.")


def _mol_from_smiles(smiles: str):  # type: ignore[return]
    """Parse SMILES and raise MoleculeValidationError if invalid."""
    if not _RDKIT_AVAILABLE:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise MoleculeValidationError(f"Invalid SMILES: {smiles}")
    return mol


class ChemoinformaticsService:
    """Service layer for all chemoinformatics operations."""

    def __init__(self) -> None:
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    # ------------------------------------------------------------------
    # Molecule analysis
    # ------------------------------------------------------------------

    async def analyze_molecule(self, smiles: str) -> Dict[str, Any]:
        """
        Parse a SMILES string and return basic molecular information.

        Args:
            smiles: SMILES string (e.g. "CCO").

        Returns:
            dict with formula, molecular weight, canonical SMILES, validity.
        """
        if not _RDKIT_AVAILABLE:
            return self._fallback_analyze(smiles)

        mol = _mol_from_smiles(smiles)
        canonical = Chem.MolToSmiles(mol)
        inchi = Chem.MolToInchi(mol)
        inchi_key = Chem.InchiToInchiKey(inchi) if inchi else None

        return {
            "smiles": smiles,
            "canonical_smiles": canonical,
            "inchi": inchi,
            "inchi_key": inchi_key,
            "formula": CalcMolFormula(mol),
            "heavy_atom_count": mol.GetNumHeavyAtoms(),
            "is_valid": True,
        }

    @staticmethod
    def _fallback_analyze(smiles: str) -> Dict[str, Any]:
        """Basic SMILES analysis without RDKit."""
        return {
            "smiles": smiles,
            "canonical_smiles": smiles,
            "inchi": None,
            "inchi_key": None,
            "formula": None,
            "heavy_atom_count": None,
            "is_valid": True,
            "note": "RDKit not available; limited analysis.",
        }

    # ------------------------------------------------------------------
    # Descriptors
    # ------------------------------------------------------------------

    async def compute_descriptors(self, smiles: str) -> Dict[str, Any]:
        """
        Compute comprehensive 2-D molecular descriptors.

        Args:
            smiles: SMILES string.

        Returns:
            dict of descriptors including Lipinski and Veber assessments.
        """
        if not _RDKIT_AVAILABLE:
            return {"smiles": smiles, "error": "RDKit not available."}
        mol = _mol_from_smiles(smiles)
        return await asyncio.to_thread(compute_all_descriptors, mol)

    # ------------------------------------------------------------------
    # Fingerprints
    # ------------------------------------------------------------------

    async def compute_fingerprint(
        self,
        smiles: str,
        fp_type: str = "morgan",
        radius: int = 2,
        n_bits: int = 2048,
    ) -> Dict[str, Any]:
        """
        Compute a molecular fingerprint bit vector.

        Args:
            smiles: SMILES string.
            fp_type: "morgan" | "maccs" | "rdkit"
            radius: Morgan fingerprint radius (ignored for others).
            n_bits: Fingerprint length in bits.

        Returns:
            dict with fp_type and bit_vector list.
        """
        if not _RDKIT_AVAILABLE:
            return {"smiles": smiles, "fp_type": fp_type, "bit_vector": []}

        mol = _mol_from_smiles(smiles)
        fp_type = fp_type.lower()

        if fp_type == "morgan":
            gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
            fp = gen.GetFingerprint(mol)
        elif fp_type == "maccs":
            fp = MACCSkeys.GenMACCSKeys(mol)
        elif fp_type == "rdkit":
            gen = rdFingerprintGenerator.GetRDKitFPGenerator(fpSize=n_bits)
            fp = gen.GetFingerprint(mol)
        else:
            raise MoleculeValidationError(
                f"Unknown fingerprint type: {fp_type}. Use morgan, maccs, or rdkit."
            )

        bit_vector = list(fp.ToBitString())
        return {
            "smiles": smiles,
            "fp_type": fp_type,
            "n_bits": len(bit_vector),
            "bit_vector": [int(b) for b in bit_vector],
            "on_bits": sum(int(b) for b in bit_vector),
        }

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    async def similarity_search(
        self,
        query_smiles: str,
        library: List[str],
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Compute Tanimoto similarity between the query and a library of SMILES.

        Args:
            query_smiles: Query molecule SMILES.
            library: List of candidate SMILES.
            threshold: Minimum similarity score to include in results.

        Returns:
            dict with ranked hits above threshold.
        """
        if not _RDKIT_AVAILABLE:
            return {"query": query_smiles, "hits": [], "note": "RDKit not available."}

        query_mol = _mol_from_smiles(query_smiles)
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        query_fp = gen.GetFingerprint(query_mol)

        hits = []
        for smiles in library:
            try:
                mol = _mol_from_smiles(smiles)
                fp = gen.GetFingerprint(mol)
                score = DataStructs.TanimotoSimilarity(query_fp, fp)
                if score >= threshold:
                    hits.append({"smiles": smiles, "tanimoto": round(score, 4)})
            except MoleculeValidationError:
                continue

        hits.sort(key=lambda x: x["tanimoto"], reverse=True)
        return {
            "query": query_smiles,
            "library_size": len(library),
            "threshold": threshold,
            "hits_found": len(hits),
            "hits": hits,
        }

    # ------------------------------------------------------------------
    # PubChem
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_pubchem(self, cid: int) -> Dict[str, Any]:
        """
        Retrieve compound property data from PubChem.

        Args:
            cid: PubChem Compound ID.

        Raises:
            ExternalAPIError: On API failure.
        """
        props = "MolecularFormula,MolecularWeight,IUPACName,IsomericSMILES,InChI,InChIKey,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount"
        url = f"{settings.PUBCHEM_BASE_URL}/compound/cid/{cid}/property/{props}/JSON"
        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError("PubChem", str(exc)) from exc
        except httpx.RequestError as exc:
            raise ExternalAPIError("PubChem", f"Network error: {exc}") from exc

        props_list = data.get("PropertyTable", {}).get("Properties", [])
        return props_list[0] if props_list else {"cid": cid}

    # ------------------------------------------------------------------
    # ADMET prediction
    # ------------------------------------------------------------------

    async def predict_admet(self, smiles: str) -> Dict[str, Any]:
        """
        Predict ADMET properties using rule-based methods.

        - Absorption: Lipinski RO5, Veber rules
        - Distribution: logP, TPSA
        - Metabolism: CYP alert patterns (simplified)
        - Excretion: MW
        - Toxicity: PAINS alert check (simplified)
        """
        if not _RDKIT_AVAILABLE:
            return {"smiles": smiles, "error": "RDKit not available."}

        mol = _mol_from_smiles(smiles)
        desc = MolecularDescriptors()
        lipinski = desc.compute_lipinski(mol)
        veber = desc.compute_veber(mol)
        core = desc.compute_2d_descriptors(mol)

        mw = core.get("molecular_weight", 0.0)
        logp = core.get("logp", 0.0)
        tpsa = core.get("tpsa", 0.0)

        return {
            "smiles": smiles,
            "absorption": {
                "oral_bioavailability_likely": lipinski["lipinski_pass"] and veber["veber_pass"],
                "lipinski": lipinski,
                "veber": veber,
            },
            "distribution": {
                "logp": round(logp, 2),
                "tpsa": round(tpsa, 2),
                "bbb_penetrant_likely": logp < 3 and tpsa < 90,
            },
            "excretion": {
                "molecular_weight": round(mw, 2),
                "rapid_clearance_risk": mw < 300 or logp < 0,
            },
            "toxicity": {
                "alerts": self._check_toxicity_alerts(mol),
            },
        }

    @staticmethod
    def _check_toxicity_alerts(mol: Any) -> List[str]:
        """Check for common structural toxicity alerts (simplified PAINS)."""
        alerts: List[str] = []
        if not _RDKIT_AVAILABLE:
            return alerts

        alert_smarts = {
            "Michael acceptor": "[$([CH]=[CH]C=O)]",
            "Reactive aldehyde": "[CX3H1](=O)",
            "Epoxide": "[OX2r3][CX4r3][CX4r3]",
            "Quinone": "O=C1C=CC(=O)C=C1",
        }
        for name, smarts in alert_smarts.items():
            patt = Chem.MolFromSmarts(smarts)
            if patt and mol.HasSubstructMatch(patt):
                alerts.append(name)
        return alerts
