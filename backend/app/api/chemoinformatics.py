"""Chemoinformatics REST endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends, Path, Query

from app.dependencies import rate_limiter
from app.services.chemoinformatics.service import ChemoinformaticsService

logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(rate_limiter)])
_svc = ChemoinformaticsService()


# ---------------------------------------------------------------------------
# Request models (inline for simplicity – full models in pydantic_models.py)
# ---------------------------------------------------------------------------
from pydantic import BaseModel, Field


class SmilesRequest(BaseModel):
    """SMILES input."""
    smiles: str = Field(..., description="SMILES string, e.g. CCO")


class SimilarityRequest(BaseModel):
    """Similarity search input."""
    query_smiles: str = Field(..., description="Query SMILES string")
    library: List[str] = Field(..., description="List of SMILES to search against")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class FingerprintRequest(BaseModel):
    """Fingerprint computation input."""
    smiles: str
    fp_type: str = Field(default="morgan", description="morgan | maccs | rdkit")
    radius: int = Field(default=2, ge=1, le=4, description="Morgan fingerprint radius")
    n_bits: int = Field(default=2048, ge=512, le=4096)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/molecule/analyze", summary="Analyze a molecule from SMILES")
async def analyze_molecule(body: SmilesRequest) -> Dict[str, Any]:
    """
    Parse a SMILES string and return basic molecular information:
    formula, molecular weight, canonical SMILES, and validity flag.
    """
    return await _svc.analyze_molecule(body.smiles)


@router.post("/molecule/descriptors", summary="Compute 2-D molecular descriptors")
async def compute_descriptors(body: SmilesRequest) -> Dict[str, Any]:
    """
    Calculate a comprehensive set of 2-D molecular descriptors including
    MW, logP, HBD, HBA, TPSA, rotatable bonds, and Lipinski/Veber flags.
    """
    return await _svc.compute_descriptors(body.smiles)


@router.post("/fingerprint", summary="Compute molecular fingerprint")
async def compute_fingerprint(body: FingerprintRequest) -> Dict[str, Any]:
    """
    Compute a binary or count molecular fingerprint (Morgan, MACCS, or RDKit)
    and return it as a bit vector list.
    """
    return await _svc.compute_fingerprint(
        body.smiles, body.fp_type, body.radius, body.n_bits
    )


@router.post("/similarity/search", summary="Tanimoto similarity search")
async def similarity_search(body: SimilarityRequest) -> Dict[str, Any]:
    """
    Compute Tanimoto similarity between a query molecule and a library of
    SMILES strings and return matches above the threshold, ranked by score.
    """
    return await _svc.similarity_search(
        body.query_smiles, body.library, body.threshold
    )


@router.get("/pubchem/{cid}", summary="Fetch PubChem compound data")
async def get_pubchem(
    cid: int = Path(..., description="PubChem Compound ID (CID)"),
) -> Dict[str, Any]:
    """Retrieve compound properties from PubChem REST API."""
    return await _svc.fetch_pubchem(cid)


@router.post("/admet/predict", summary="Predict ADMET properties")
async def predict_admet(body: SmilesRequest) -> Dict[str, Any]:
    """
    Predict absorption, distribution, metabolism, excretion, and toxicity
    (ADMET) properties using rule-based models (Lipinski, Veber, PAINS).
    """
    return await _svc.predict_admet(body.smiles)
