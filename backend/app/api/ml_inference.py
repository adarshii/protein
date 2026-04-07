"""ML inference REST endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import rate_limiter
from app.services.ml_inference.service import MLInferenceService
from app.services.ml_inference.embeddings import DrugEmbedder, ProteinEmbedder

logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(rate_limiter)])

_ml_svc = MLInferenceService()
_prot_embedder = ProteinEmbedder()
_drug_embedder = DrugEmbedder()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ProteinEmbedRequest(BaseModel):
    sequence: str = Field(..., description="Amino-acid sequence (single letter)")
    method: str = Field(default="kmer", description="kmer | onehot")


class DrugEmbedRequest(BaseModel):
    smiles: str = Field(..., description="SMILES string")
    fp_type: str = Field(default="morgan", description="morgan | maccs | rdkit")


class DTIRequest(BaseModel):
    protein_sequence: str
    smiles: str


class ToxicityRequest(BaseModel):
    smiles: str
    models: List[str] = Field(
        default=["ames", "herg", "hepatotoxicity"],
        description="Toxicity endpoints to predict",
    )


class ExplainRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature name → value map")
    prediction: float = Field(..., description="Model prediction to explain")
    top_k: int = Field(default=10, ge=1, le=50)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/protein/embed", summary="Generate protein sequence embeddings")
async def embed_protein(body: ProteinEmbedRequest) -> Dict[str, Any]:
    """
    Encode a protein sequence as a fixed-length numerical vector using
    k-mer frequency or one-hot encoding.
    """
    embedding = _prot_embedder.encode(body.sequence, method=body.method)
    return {
        "sequence_length": len(body.sequence),
        "embedding_dim": len(embedding),
        "method": body.method,
        "embedding": embedding,
    }


@router.post("/drug/embed", summary="Generate drug molecular embeddings")
async def embed_drug(body: DrugEmbedRequest) -> Dict[str, Any]:
    """
    Encode a molecule (SMILES) as a binary fingerprint vector.
    """
    embedding = _drug_embedder.encode(body.smiles, fp_type=body.fp_type)
    return {
        "smiles": body.smiles,
        "embedding_dim": len(embedding),
        "fp_type": body.fp_type,
        "embedding": embedding,
    }


@router.post("/dti/predict", summary="Drug-target interaction prediction")
async def predict_dti(body: DTIRequest) -> Dict[str, Any]:
    """
    Predict whether a small molecule (SMILES) will interact with a given
    protein sequence. Returns a probability score and feature importances.
    """
    return await _ml_svc.predict_dti(body.protein_sequence, body.smiles)


@router.post("/toxicity/predict", summary="Multi-endpoint toxicity prediction")
async def predict_toxicity(body: ToxicityRequest) -> Dict[str, Any]:
    """
    Predict toxicity across multiple endpoints using molecular descriptors
    and rule-based heuristics.
    """
    return await _ml_svc.predict_toxicity(body.smiles, body.models)


@router.post("/explain", summary="Feature importance / SHAP explanation")
async def explain_prediction(body: ExplainRequest) -> Dict[str, Any]:
    """
    Compute SHAP-style feature importances for a model prediction given a
    feature dictionary and the predicted value.
    """
    return await _ml_svc.explain_prediction(body.features, body.prediction, body.top_k)
