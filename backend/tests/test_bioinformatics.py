"""Unit tests for the bioinformatics service and utility functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.bioinformatics.utils import (
    calculate_gc_content,
    find_start_codons,
    reverse_complement,
    transcribe,
    translate_sequence,
    validate_sequence,
)


# ---------------------------------------------------------------------------
# calculate_gc_content
# ---------------------------------------------------------------------------


def test_calculate_gc_content_basic():
    assert calculate_gc_content("ATGC") == 50.0


def test_calculate_gc_content_all_gc():
    assert calculate_gc_content("GCGCGC") == 100.0


def test_calculate_gc_content_no_gc():
    assert calculate_gc_content("ATATAT") == 0.0


def test_calculate_gc_content_empty():
    assert calculate_gc_content("") == 0.0


def test_calculate_gc_content_case_insensitive():
    assert calculate_gc_content("atgc") == calculate_gc_content("ATGC")


# ---------------------------------------------------------------------------
# validate_sequence
# ---------------------------------------------------------------------------


def test_validate_dna_sequence_valid():
    valid, msg = validate_sequence("ATGCATGCNN", "dna")
    assert valid is True
    assert msg == ""


def test_validate_dna_sequence_invalid():
    valid, msg = validate_sequence("ATGCZZZ", "dna")
    assert valid is False
    assert "Z" in msg


def test_validate_dna_sequence_with_n():
    valid, _ = validate_sequence("ATGNNN", "dna")
    assert valid is True


def test_validate_rna_sequence_valid():
    valid, _ = validate_sequence("AUGCAUGC", "rna")
    assert valid is True


def test_validate_protein_sequence_valid():
    valid, _ = validate_sequence("MKALIVLGLV", "protein")
    assert valid is True


def test_validate_protein_sequence_stop_codon():
    valid, _ = validate_sequence("MKALIV*", "protein")
    assert valid is True


def test_validate_sequence_unknown_type():
    valid, msg = validate_sequence("ATGC", "nucleotide")
    assert valid is False
    assert "Unknown" in msg


# ---------------------------------------------------------------------------
# reverse_complement
# ---------------------------------------------------------------------------


def test_reverse_complement_basic():
    assert reverse_complement("ATGC") == "GCAT"


def test_reverse_complement_palindrome():
    seq = "GAATTC"  # EcoRI site
    assert reverse_complement(seq) == "GAATTC"


def test_reverse_complement_with_n():
    result = reverse_complement("ATGN")
    assert "N" in result


def test_reverse_complement_lowercase():
    assert reverse_complement("atgc") == "GCAT"


# ---------------------------------------------------------------------------
# transcribe
# ---------------------------------------------------------------------------


def test_transcribe_basic():
    assert transcribe("ATGC") == "AUGC"


def test_transcribe_no_thymine():
    result = transcribe("AAAA")
    assert "T" not in result
    assert result == "AAAA"


def test_transcribe_lowercase():
    assert transcribe("atgc") == "AUGC"


# ---------------------------------------------------------------------------
# translate_sequence
# ---------------------------------------------------------------------------


def test_translate_sequence_met_start():
    # ATG → M
    result = translate_sequence("ATGGCC")
    assert result.startswith("M")


def test_translate_sequence_stops_at_stop_codon():
    # ATG GCC TAA GCC — should stop at TAA
    result = translate_sequence("ATGGCCTAAGCC")
    assert "*" not in result
    assert result == "MA"


def test_translate_sequence_empty():
    assert translate_sequence("") == ""


# ---------------------------------------------------------------------------
# find_start_codons
# ---------------------------------------------------------------------------


def test_find_start_codons_single():
    positions = find_start_codons("ATGGCC")
    assert 0 in positions


def test_find_start_codons_multiple():
    # "ATGAAATG": first ATG at 0, second ATG at 5
    positions = find_start_codons("ATGAAATG")
    assert 0 in positions
    assert 5 in positions


def test_find_start_codons_none():
    positions = find_start_codons("GCGGCGGCG")
    assert positions == []


# ---------------------------------------------------------------------------
# BioinformaticsService — mocked async tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_sequence_dna_via_service():
    from app.services.bioinformatics.service import BioinformaticsService
    from app.services.bioinformatics.models import SequenceType

    svc = BioinformaticsService()
    result = await svc.analyze_sequence("ATGCATGC", SequenceType.DNA)
    assert result.length == 8
    assert result.gc_content == 50.0
    assert result.is_valid is True


@pytest.mark.asyncio
async def test_analyze_sequence_invalid_raises():
    from app.services.bioinformatics.service import BioinformaticsService
    from app.services.bioinformatics.models import SequenceType
    from app.exception_handlers import SequenceValidationError

    svc = BioinformaticsService()
    with pytest.raises(SequenceValidationError):
        await svc.analyze_sequence("ATGCZZZ", SequenceType.DNA)


@pytest.mark.asyncio
async def test_find_orfs_returns_list():
    from app.services.bioinformatics.service import BioinformaticsService

    # 105 nt ORF: ATG + 34 codons + TAA
    dna = "ATG" + ("GCT" * 34) + "TAA"
    svc = BioinformaticsService()
    orfs = await svc.find_orfs(dna, min_length=100)
    assert isinstance(orfs, list)
    assert len(orfs) >= 1
    assert orfs[0].strand in ("+", "-")


@pytest.mark.asyncio
async def test_find_orfs_empty_for_short_sequence():
    from app.services.bioinformatics.service import BioinformaticsService

    svc = BioinformaticsService()
    orfs = await svc.find_orfs("ATGGCCTAA", min_length=100)
    assert orfs == []


@pytest.mark.asyncio
async def test_translate_dna_via_service():
    from app.services.bioinformatics.service import BioinformaticsService

    svc = BioinformaticsService()
    protein = await svc.translate_dna("ATGGCCTAA")
    assert protein == "MA"
