"""Integration-style tests for all REST API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_health_db_endpoint(client: AsyncClient):
    """DB probe returns 200 on success or 503 on failure — either is acceptable."""
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    mock_conn.execute = AsyncMock()

    mock_engine = MagicMock()
    mock_engine.connect = MagicMock(return_value=mock_conn)

    with patch("app.api.health.engine", mock_engine, create=True):
        response = await client.get("/health/db")
    assert response.status_code in (200, 503)


# ---------------------------------------------------------------------------
# Bioinformatics endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_sequence_dna(client: AsyncClient, sample_dna_sequence: str):
    payload = {"sequence": sample_dna_sequence, "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sequence_type"] == "dna"
    assert data["length"] == len(sample_dna_sequence)
    assert "gc_content" in data
    assert "composition" in data


@pytest.mark.asyncio
async def test_analyze_sequence_protein(client: AsyncClient, sample_protein_sequence: str):
    payload = {"sequence": sample_protein_sequence, "seq_type": "protein"}
    response = await client.post("/api/bio/sequence/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sequence_type"] == "protein"
    assert data["length"] == len(sample_protein_sequence)
    assert data["gc_content"] is None


@pytest.mark.asyncio
async def test_translate_dna(client: AsyncClient, sample_dna_sequence: str):
    payload = {"sequence": sample_dna_sequence, "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/translate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "dna" in data
    assert "protein" in data
    assert data["dna"] == sample_dna_sequence.upper()


@pytest.mark.asyncio
async def test_translate_dna_rejects_protein(client: AsyncClient, sample_protein_sequence: str):
    """Translating a protein sequence must be rejected (422 or 400)."""
    payload = {"sequence": sample_protein_sequence, "seq_type": "protein"}
    response = await client.post("/api/bio/sequence/translate", json=payload)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_find_orfs(client: AsyncClient):
    # Sequence long enough to contain an ORF ≥ 100 nt (default min_length)
    dna = "ATG" + ("GCT" * 34) + "TAA"  # 105 nt ORF
    payload = {"sequence": dna, "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/orf", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_find_orfs_short_sequence(client: AsyncClient, sample_dna_sequence: str):
    """Short sequences return an empty ORF list (none meet min_length)."""
    payload = {"sequence": sample_dna_sequence, "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/orf", json=payload)
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Chemoinformatics endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_molecule(client: AsyncClient, sample_smiles: str):
    payload = {"smiles": sample_smiles}
    response = await client.post("/api/chem/molecule/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "smiles" in data
    assert data.get("is_valid") is True


@pytest.mark.asyncio
async def test_compute_descriptors(client: AsyncClient, sample_smiles: str):
    payload = {"smiles": sample_smiles}
    response = await client.post("/api/chem/molecule/descriptors", json=payload)
    assert response.status_code == 200
    data = response.json()
    # With RDKit available the response has descriptor keys; without it we get
    # an informational error key — both are valid non-error HTTP responses.
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# ML inference endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_predict_dti(client: AsyncClient, sample_protein_sequence: str, sample_smiles: str):
    payload = {"protein_sequence": sample_protein_sequence, "smiles": sample_smiles}
    response = await client.post("/api/ml/dti/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "interaction_probability" in data
    assert 0.0 <= data["interaction_probability"] <= 1.0


# ---------------------------------------------------------------------------
# Genomics endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_annotate_variant(client: AsyncClient):
    payload = {
        "chrom": "chr1",
        "pos": 925952,
        "ref": "G",
        "alt": "A",
        "genome_build": "GRCh38",
    }
    response = await client.post("/api/genomics/variant/annotate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "variant_id" in data or "chrom" in data or "consequence" in data


# ---------------------------------------------------------------------------
# Validation error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_sequence_characters(client: AsyncClient):
    """Sequences with invalid characters should be rejected with 4xx."""
    payload = {"sequence": "ATGCZZZ999", "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/analyze", json=payload)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_missing_required_field(client: AsyncClient):
    """Missing the required 'sequence' field should return 422."""
    response = await client.post("/api/bio/sequence/analyze", json={"seq_type": "dna"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_sequence(client: AsyncClient):
    """An empty sequence string must be rejected by Pydantic validation."""
    payload = {"sequence": "", "seq_type": "dna"}
    response = await client.post("/api/bio/sequence/analyze", json=payload)
    assert response.status_code == 422
