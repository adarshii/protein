"""Comprehensive Pydantic schemas for API request/response contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Common / base models
# ---------------------------------------------------------------------------


class TimestampedModel(BaseModel):
    """Base model with created_at and updated_at fields."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ErrorDetail(BaseModel):
    """Single error detail entry."""

    loc: Optional[List[str]] = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """Structured error response envelope."""

    error: Dict[str, Any]
    status_code: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ---------------------------------------------------------------------------
# Auth / User
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed).")
        return v


class UserResponse(TimestampedModel):
    """User data returned to clients."""

    id: int
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


class SequenceType(str, Enum):
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"


class SequenceRequest(BaseModel):
    """Request to analyse or process a biological sequence."""

    sequence: str = Field(..., min_length=1, max_length=100_000)
    seq_type: SequenceType = SequenceType.DNA
    label: Optional[str] = Field(None, max_length=256, description="Optional sequence label")

    @field_validator("sequence")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().upper().replace(" ", "").replace("\n", "")


class SequenceResponse(BaseModel):
    """Generic sequence analysis response."""

    sequence_type: str
    length: int
    gc_content: Optional[float] = None
    composition: Dict[str, int] = {}
    molecular_weight_da: float
    is_valid: bool
    label: Optional[str] = None


# ---------------------------------------------------------------------------
# Molecule
# ---------------------------------------------------------------------------


class MoleculeRequest(BaseModel):
    """Request to analyse or process a chemical structure."""

    smiles: str = Field(..., min_length=1, description="SMILES string")
    name: Optional[str] = Field(None, max_length=256)


class MoleculeResponse(BaseModel):
    """Molecule analysis response."""

    smiles: str
    canonical_smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchi_key: Optional[str] = None
    formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    is_valid: bool
    descriptors: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# ML
# ---------------------------------------------------------------------------


class MLPredictionRequest(BaseModel):
    """Generic ML inference request."""

    protein_sequence: Optional[str] = None
    smiles: Optional[str] = None
    features: Optional[Dict[str, float]] = None
    model_name: Optional[str] = None


class MLPredictionResponse(BaseModel):
    """Generic ML inference response."""

    prediction: Any
    confidence: Optional[float] = None
    model: Optional[str] = None
    feature_importances: Optional[Dict[str, float]] = None
    explanation: Optional[str] = None


# ---------------------------------------------------------------------------
# Genomics
# ---------------------------------------------------------------------------


class VariantRequest(BaseModel):
    """Variant annotation request."""

    chrom: str
    pos: int = Field(..., ge=1)
    ref: str = Field(..., min_length=1)
    alt: str = Field(..., min_length=1)
    genome_build: str = "GRCh38"


class GenomicsResponse(BaseModel):
    """Generic genomics endpoint response."""

    data: Dict[str, Any]
    source: Optional[str] = None
    genome_build: Optional[str] = None


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Create an async analysis job."""

    job_type: str
    input_data: Optional[Dict[str, Any]] = None


class JobResult(TimestampedModel):
    """Analysis job record returned to clients."""

    id: str
    job_type: str
    status: JobStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
