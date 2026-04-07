"""Genomics REST endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from app.dependencies import rate_limiter
from app.services.genomics.service import GenomicsService

logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(rate_limiter)])
_svc = GenomicsService()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class VariantAnnotationRequest(BaseModel):
    """Single variant annotation request (1-based coordinates)."""
    chrom: str = Field(..., description="Chromosome (e.g. chr1, 1)")
    pos: int = Field(..., ge=1, description="Position (1-based)")
    ref: str = Field(..., min_length=1, description="Reference allele")
    alt: str = Field(..., min_length=1, description="Alternate allele")
    genome_build: str = Field(default="GRCh38", description="GRCh37 | GRCh38")


class SNPAnalysisRequest(BaseModel):
    """SNP analysis by rsID."""
    rsid: str = Field(..., description="dbSNP rsID, e.g. rs1234567")


class PathwayEnrichmentRequest(BaseModel):
    """Pathway enrichment analysis request."""
    gene_list: List[str] = Field(..., min_length=1, description="HGNC gene symbols")
    background_size: Optional[int] = Field(
        default=20000, description="Background genome size"
    )
    p_value_threshold: float = Field(default=0.05, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/variant/annotate", summary="Annotate a genomic variant")
async def annotate_variant(body: VariantAnnotationRequest) -> Dict[str, Any]:
    """
    Annotate a single nucleotide or indel variant with predicted functional
    impact, affected genes, transcript consequences, and population frequency.
    """
    return await _svc.annotate_variant(
        body.chrom, body.pos, body.ref, body.alt, body.genome_build
    )


@router.post("/snp/analyze", summary="Analyse a SNP by rsID")
async def analyze_snp(body: SNPAnalysisRequest) -> Dict[str, Any]:
    """
    Retrieve allele frequency, clinical significance, and functional
    annotation for a dbSNP variant.
    """
    return await _svc.analyze_snp(body.rsid)


@router.get("/gene/{gene_id}", summary="Retrieve gene information")
async def get_gene_info(
    gene_id: str = Path(..., description="HGNC symbol or Ensembl ID"),
    include_transcripts: bool = Query(default=False),
) -> Dict[str, Any]:
    """
    Fetch gene-level information including chromosomal location, biotype,
    associated diseases, and optionally transcript annotations.
    """
    return await _svc.get_gene_info(gene_id, include_transcripts=include_transcripts)


@router.post("/pathway/enrichment", summary="Pathway enrichment analysis")
async def pathway_enrichment(body: PathwayEnrichmentRequest) -> Dict[str, Any]:
    """
    Perform over-representation analysis against KEGG / Reactome pathways
    for a supplied gene list and return significantly enriched pathways
    with adjusted p-values.
    """
    return await _svc.pathway_enrichment(
        body.gene_list,
        background_size=body.background_size,
        p_value_threshold=body.p_value_threshold,
    )
