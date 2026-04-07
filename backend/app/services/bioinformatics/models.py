"""Pydantic models for the bioinformatics service."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SequenceType(str, Enum):
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"


class AlignmentAlgorithm(str, Enum):
    NEEDLEMAN_WUNSCH = "needleman_wunsch"
    SMITH_WATERMAN = "smith_waterman"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


class SequenceInput(BaseModel):
    """Input for sequence analysis endpoints."""

    sequence: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="Biological sequence string",
    )
    seq_type: SequenceType = Field(
        default=SequenceType.DNA,
        description="Sequence type: dna, rna, or protein",
    )

    @field_validator("sequence")
    @classmethod
    def strip_whitespace_and_upper(cls, v: str) -> str:
        """Normalize sequence: strip whitespace and uppercase."""
        return v.strip().upper().replace(" ", "").replace("\n", "")


class AlignmentInput(BaseModel):
    """Input for pairwise alignment."""

    sequence1: str = Field(..., min_length=1, max_length=10_000)
    sequence2: str = Field(..., min_length=1, max_length=10_000)
    algorithm: AlignmentAlgorithm = AlignmentAlgorithm.NEEDLEMAN_WUNSCH
    match_score: float = Field(default=2.0)
    mismatch_score: float = Field(default=-1.0)
    gap_open: float = Field(default=-0.5)
    gap_extend: float = Field(default=-0.1)

    @field_validator("sequence1", "sequence2")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().upper()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class SequenceAnalysisResult(BaseModel):
    """Output from sequence analysis."""

    sequence_type: SequenceType
    length: int
    composition: Dict[str, int]
    composition_percent: Dict[str, float]
    gc_content: Optional[float] = Field(
        None, description="GC percentage (DNA/RNA only)"
    )
    molecular_weight_da: float = Field(description="Estimated molecular weight (Da)")
    is_valid: bool


class ORFResult(BaseModel):
    """Single open reading frame."""

    strand: str = Field(description="+ or -")
    start: int = Field(description="0-based start position on forward strand")
    stop: int = Field(description="0-based stop position (exclusive)")
    length_nt: int
    length_aa: int
    protein_sequence: str


class AlignmentResult(BaseModel):
    """Pairwise alignment output."""

    algorithm: str
    score: float
    aligned_seq1: str
    aligned_seq2: str
    identity_percent: float
    similarity_percent: float
    gaps: int
    length: int


class UniProtData(BaseModel):
    """Simplified UniProt entry."""

    accession: str
    entry_name: Optional[str] = None
    protein_name: Optional[str] = None
    gene_names: List[str] = []
    organism: Optional[str] = None
    sequence: Optional[str] = None
    sequence_length: Optional[int] = None
    function: Optional[str] = None
    raw: Optional[Dict[str, Any]] = Field(None, exclude=True)


class AlphaFoldData(BaseModel):
    """AlphaFold structure metadata."""

    uniprot_id: str
    entry_id: Optional[str] = None
    pdb_url: Optional[str] = None
    cif_url: Optional[str] = None
    pae_image_url: Optional[str] = None
    plddt_score: Optional[float] = None
    model_created_date: Optional[str] = None
