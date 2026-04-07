"""Bioinformatics service — core business logic."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exception_handlers import ExternalAPIError, SequenceValidationError
from app.services.bioinformatics.models import (
    AlignmentAlgorithm,
    AlignmentInput,
    AlignmentResult,
    AlphaFoldData,
    ORFResult,
    SequenceAnalysisResult,
    SequenceType,
    UniProtData,
)
from app.services.bioinformatics.utils import (
    calculate_gc_content,
    calculate_molecular_weight,
    find_start_codons,
    reverse_complement,
    translate_sequence,
    validate_sequence,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional biopython imports
# ---------------------------------------------------------------------------
try:
    from Bio import pairwise2
    from Bio.pairwise2 import format_alignment
    from Bio.SeqUtils import gc_fraction
    _BIO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BIO_AVAILABLE = False
    logger.warning("biopython_not_available", msg="Falling back to built-in implementations.")


class BioinformaticsService:
    """Service layer for all bioinformatics operations."""

    def __init__(self) -> None:
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    # ------------------------------------------------------------------
    # Sequence analysis
    # ------------------------------------------------------------------

    async def analyze_sequence(
        self, sequence: str, seq_type: SequenceType
    ) -> SequenceAnalysisResult:
        """
        Compute basic metrics for a biological sequence.

        Args:
            sequence: The raw sequence string (already normalized).
            seq_type: DNA, RNA, or PROTEIN.

        Returns:
            SequenceAnalysisResult with composition and biophysical properties.
        """
        is_valid, error_msg = validate_sequence(sequence, seq_type.value)
        if not is_valid:
            raise SequenceValidationError(error_msg)

        composition: Dict[str, int] = {}
        for char in sequence:
            composition[char] = composition.get(char, 0) + 1

        total = len(sequence)
        composition_pct = {
            k: round(v / total * 100, 2) for k, v in composition.items()
        }

        gc = None
        if seq_type in (SequenceType.DNA, SequenceType.RNA):
            gc = calculate_gc_content(sequence)

        mw = calculate_molecular_weight(sequence, seq_type.value)

        return SequenceAnalysisResult(
            sequence_type=seq_type,
            length=total,
            composition=composition,
            composition_percent=composition_pct,
            gc_content=gc,
            molecular_weight_da=mw,
            is_valid=True,
        )

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    async def translate_dna(self, sequence: str) -> str:
        """
        Translate a DNA coding sequence to protein using the standard genetic code.

        Args:
            sequence: DNA sequence (5'→3'), multiple of 3 preferred.

        Returns:
            Single-letter amino acid string, stops before first stop codon.
        """
        is_valid, err = validate_sequence(sequence, "dna")
        if not is_valid:
            raise SequenceValidationError(err)
        return translate_sequence(sequence)

    # ------------------------------------------------------------------
    # ORF detection
    # ------------------------------------------------------------------

    async def find_orfs(
        self, sequence: str, min_length: int = 100
    ) -> List[ORFResult]:
        """
        Find all ORFs on both strands of a DNA sequence.

        Args:
            sequence: DNA sequence.
            min_length: Minimum ORF length in nucleotides.

        Returns:
            List of ORFResult objects, sorted by length descending.
        """
        is_valid, err = validate_sequence(sequence, "dna")
        if not is_valid:
            raise SequenceValidationError(err)

        stop_codons = {"TAA", "TAG", "TGA"}
        orfs: List[ORFResult] = []

        for strand_seq, strand_label in [
            (sequence, "+"),
            (reverse_complement(sequence), "-"),
        ]:
            for start in find_start_codons(strand_seq):
                for j in range(start, len(strand_seq) - 2, 3):
                    codon = strand_seq[j : j + 3]
                    if codon in stop_codons:
                        orf_nt = strand_seq[start : j + 3]
                        if len(orf_nt) >= min_length:
                            protein = translate_sequence(orf_nt)
                            # Map back to forward strand positions
                            if strand_label == "+":
                                fwd_start, fwd_stop = start, j + 3
                            else:
                                seq_len = len(sequence)
                                fwd_stop = seq_len - start
                                fwd_start = seq_len - (j + 3)

                            orfs.append(
                                ORFResult(
                                    strand=strand_label,
                                    start=fwd_start,
                                    stop=fwd_stop,
                                    length_nt=len(orf_nt),
                                    length_aa=len(protein),
                                    protein_sequence=protein,
                                )
                            )
                        break

        return sorted(orfs, key=lambda o: o.length_nt, reverse=True)

    # ------------------------------------------------------------------
    # Pairwise alignment
    # ------------------------------------------------------------------

    async def pairwise_alignment(
        self,
        seq1: str,
        seq2: str,
        algorithm: AlignmentAlgorithm = AlignmentAlgorithm.NEEDLEMAN_WUNSCH,
    ) -> AlignmentResult:
        """
        Perform global (Needleman-Wunsch) or local (Smith-Waterman) pairwise alignment.

        Falls back to a simple built-in implementation if BioPython is unavailable.
        """
        if _BIO_AVAILABLE:
            return await asyncio.to_thread(
                self._bio_pairwise_alignment, seq1, seq2, algorithm
            )
        return self._builtin_pairwise_alignment(seq1, seq2, algorithm)

    def _bio_pairwise_alignment(
        self, seq1: str, seq2: str, algorithm: AlignmentAlgorithm
    ) -> AlignmentResult:
        """BioPython-backed pairwise alignment."""
        if algorithm == AlignmentAlgorithm.NEEDLEMAN_WUNSCH:
            alignments = pairwise2.align.globalms(seq1, seq2, 2, -1, -0.5, -0.1)
        else:
            alignments = pairwise2.align.localms(seq1, seq2, 2, -1, -0.5, -0.1)

        if not alignments:
            raise SequenceValidationError("No alignment could be computed.")

        best = alignments[0]
        a1, a2 = best.seqA, best.seqB
        return self._compute_alignment_stats(a1, a2, algorithm, best.score)

    def _builtin_pairwise_alignment(
        self, seq1: str, seq2: str, algorithm: AlignmentAlgorithm
    ) -> AlignmentResult:
        """Minimal Needleman-Wunsch implementation (no external deps)."""
        n, m = len(seq1), len(seq2)
        match, mismatch, gap = 2, -1, -1
        dp = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(n + 1):
            dp[i][0] = i * gap
        for j in range(m + 1):
            dp[0][j] = j * gap

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                score = match if seq1[i - 1] == seq2[j - 1] else mismatch
                dp[i][j] = max(
                    dp[i - 1][j - 1] + score,
                    dp[i - 1][j] + gap,
                    dp[i][j - 1] + gap,
                )

        # Traceback
        a1_chars, a2_chars = [], []
        i, j = n, m
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                score = match if seq1[i - 1] == seq2[j - 1] else mismatch
                if dp[i][j] == dp[i - 1][j - 1] + score:
                    a1_chars.append(seq1[i - 1])
                    a2_chars.append(seq2[j - 1])
                    i -= 1
                    j -= 1
                elif dp[i][j] == dp[i - 1][j] + gap:
                    a1_chars.append(seq1[i - 1])
                    a2_chars.append("-")
                    i -= 1
                else:
                    a1_chars.append("-")
                    a2_chars.append(seq2[j - 1])
                    j -= 1
            elif i > 0:
                a1_chars.append(seq1[i - 1])
                a2_chars.append("-")
                i -= 1
            else:
                a1_chars.append("-")
                a2_chars.append(seq2[j - 1])
                j -= 1

        a1 = "".join(reversed(a1_chars))
        a2 = "".join(reversed(a2_chars))
        return self._compute_alignment_stats(a1, a2, algorithm, float(dp[n][m]))

    @staticmethod
    def _compute_alignment_stats(
        a1: str, a2: str, algorithm: AlignmentAlgorithm, score: float
    ) -> AlignmentResult:
        """Compute identity/similarity/gap statistics from aligned sequences."""
        length = max(len(a1), len(a2))
        pairs = list(zip(a1.ljust(length, "-"), a2.ljust(length, "-")))
        identical = sum(1 for x, y in pairs if x == y and x != "-")
        gaps = sum(1 for x, y in pairs if x == "-" or y == "-")
        return AlignmentResult(
            algorithm=algorithm.value,
            score=round(score, 2),
            aligned_seq1=a1,
            aligned_seq2=a2,
            identity_percent=round(identical / length * 100, 2) if length else 0.0,
            similarity_percent=round(identical / length * 100, 2) if length else 0.0,
            gaps=gaps,
            length=length,
        )

    # ------------------------------------------------------------------
    # External API calls
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_uniprot(self, accession: str) -> Dict[str, Any]:
        """
        Retrieve a UniProt entry in JSON format.

        Args:
            accession: UniProt accession number, e.g. "P68431".

        Raises:
            ExternalAPIError: If the UniProt API request fails.
        """
        url = f"{settings.UNIPROT_BASE_URL}/{accession}"
        try:
            resp = await self.http_client.get(url, params={"format": "json"})
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError("UniProt", str(exc)) from exc
        except httpx.RequestError as exc:
            raise ExternalAPIError("UniProt", f"Network error: {exc}") from exc

        # Extract key fields
        protein_names = data.get("proteinDescription", {})
        rec_name = protein_names.get("recommendedName", {})
        prot_name = rec_name.get("fullName", {}).get("value") if rec_name else None

        genes = [
            g.get("geneName", {}).get("value", "")
            for g in data.get("genes", [])
            if "geneName" in g
        ]

        seq_info = data.get("sequence", {})
        organism = data.get("organism", {}).get("scientificName")

        return UniProtData(
            accession=accession,
            entry_name=data.get("uniProtkbId"),
            protein_name=prot_name,
            gene_names=genes,
            organism=organism,
            sequence=seq_info.get("value"),
            sequence_length=seq_info.get("length"),
        ).model_dump()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_alphafold(self, uniprot_id: str) -> Dict[str, Any]:
        """
        Retrieve AlphaFold structure metadata for a UniProt accession.

        Args:
            uniprot_id: UniProt accession string.

        Raises:
            ExternalAPIError: If the AlphaFold API request fails.
        """
        url = f"{settings.ALPHAFOLD_BASE_URL}/prediction/{uniprot_id}"
        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            entries = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError("AlphaFold", str(exc)) from exc
        except httpx.RequestError as exc:
            raise ExternalAPIError("AlphaFold", f"Network error: {exc}") from exc

        if not entries:
            return AlphaFoldData(uniprot_id=uniprot_id).model_dump()

        entry = entries[0] if isinstance(entries, list) else entries
        return AlphaFoldData(
            uniprot_id=uniprot_id,
            entry_id=entry.get("entryId"),
            pdb_url=entry.get("pdbUrl"),
            cif_url=entry.get("cifUrl"),
            pae_image_url=entry.get("paeImageUrl"),
            plddt_score=entry.get("globalMetricValue"),
            model_created_date=entry.get("modelCreatedDate"),
        ).model_dump()
