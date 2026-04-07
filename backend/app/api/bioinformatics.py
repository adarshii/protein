"""Bioinformatics REST endpoints."""

from __future__ import annotations

from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, Path, Query

from app.dependencies import rate_limiter
from app.exception_handlers import SequenceValidationError
from app.services.bioinformatics.models import (
    AlignmentInput,
    AlignmentResult,
    ORFResult,
    SequenceAnalysisResult,
    SequenceInput,
    SequenceType,
)
from app.services.bioinformatics.service import BioinformaticsService

logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(rate_limiter)])
_svc = BioinformaticsService()


@router.post(
    "/sequence/analyze",
    response_model=SequenceAnalysisResult,
    summary="Analyze a biological sequence",
)
async def analyze_sequence(body: SequenceInput) -> SequenceAnalysisResult:
    """
    Compute basic metrics for a DNA, RNA, or protein sequence:
    length, nucleotide/amino-acid composition, GC content (nucleotides),
    and estimated molecular weight.
    """
    return await _svc.analyze_sequence(body.sequence, body.seq_type)


@router.post(
    "/sequence/translate",
    summary="Translate a DNA sequence to protein",
)
async def translate_dna(body: SequenceInput) -> Dict[str, Any]:
    """
    Translate a DNA coding sequence to a protein sequence using the
    standard genetic code. Input must be a DNA sequence.
    """
    if body.seq_type != SequenceType.DNA:
        raise SequenceValidationError("Only DNA sequences can be translated.")
    protein = await _svc.translate_dna(body.sequence)
    return {"dna": body.sequence.upper(), "protein": protein}


@router.post(
    "/sequence/orf",
    response_model=list[ORFResult],
    summary="Find open reading frames",
)
async def find_orfs(
    body: SequenceInput,
    min_length: int = Query(default=100, ge=30, description="Minimum ORF length (nt)"),
) -> list[ORFResult]:
    """
    Detect all open reading frames (ORFs) in a DNA sequence on both strands.
    Returns each ORF with its start/stop positions and translated sequence.
    """
    if body.seq_type != SequenceType.DNA:
        raise SequenceValidationError("ORF detection requires a DNA sequence.")
    return await _svc.find_orfs(body.sequence, min_length=min_length)


@router.post(
    "/alignment/pairwise",
    response_model=AlignmentResult,
    summary="Pairwise sequence alignment",
)
async def pairwise_alignment(body: AlignmentInput) -> AlignmentResult:
    """
    Perform pairwise alignment of two sequences.
    Supported algorithms: **needleman_wunsch** (global), **smith_waterman** (local).
    """
    return await _svc.pairwise_alignment(
        body.sequence1, body.sequence2, body.algorithm
    )


@router.post(
    "/structure/predict",
    summary="Request protein structure prediction",
)
async def predict_structure(body: SequenceInput) -> Dict[str, Any]:
    """
    Submit a protein sequence for structure prediction (async job).
    In production this would enqueue a Celery task.
    """
    if body.seq_type != SequenceType.PROTEIN:
        raise SequenceValidationError("Structure prediction requires a protein sequence.")
    job_id = f"struct_{hash(body.sequence) & 0xFFFFFFFF:08x}"
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Structure prediction job submitted. Poll /api/jobs/{job_id} for status.",
        "sequence_length": len(body.sequence),
    }


@router.get(
    "/uniprot/{accession}",
    summary="Fetch UniProt entry",
)
async def get_uniprot(
    accession: str = Path(..., description="UniProt accession, e.g. P68431"),
) -> Dict[str, Any]:
    """Retrieve protein annotation data from the UniProt REST API."""
    return await _svc.fetch_uniprot(accession)


@router.get(
    "/alphafold/{uniprot_id}",
    summary="Fetch AlphaFold structure metadata",
)
async def get_alphafold(
    uniprot_id: str = Path(..., description="UniProt ID, e.g. P68431"),
) -> Dict[str, Any]:
    """Retrieve predicted 3-D structure metadata from AlphaFold DB."""
    return await _svc.fetch_alphafold(uniprot_id)
