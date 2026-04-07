"""Helper utilities for bioinformatics computations."""

from __future__ import annotations

import re
from typing import Dict, Set

from app.utils.constants import (
    AMINO_ACID_WEIGHTS,
    CODON_TABLE,
    DNA_NUCLEOTIDES,
    NUCLEOTIDE_WEIGHTS,
    RNA_NUCLEOTIDES,
    AMINO_ACIDS,
)


def validate_sequence(sequence: str, seq_type: str) -> tuple[bool, str]:
    """
    Validate that a sequence only contains characters legal for its type.

    Returns:
        (is_valid, error_message) tuple.
    """
    seq = sequence.upper()
    if seq_type == "dna":
        allowed: Set[str] = DNA_NUCLEOTIDES | {"N"}
    elif seq_type == "rna":
        allowed = RNA_NUCLEOTIDES | {"N"}
    elif seq_type == "protein":
        allowed = AMINO_ACIDS | {"X", "*", "-"}
    else:
        return False, f"Unknown sequence type: {seq_type}"

    invalid = set(seq) - allowed
    if invalid:
        return False, f"Invalid characters for {seq_type}: {', '.join(sorted(invalid))}"
    return True, ""


def calculate_gc_content(sequence: str) -> float:
    """Return GC content as a percentage (0–100)."""
    seq = sequence.upper()
    if not seq:
        return 0.0
    gc = sum(1 for c in seq if c in {"G", "C"})
    return round(gc / len(seq) * 100, 2)


def calculate_molecular_weight(sequence: str, seq_type: str) -> float:
    """
    Estimate molecular weight in Daltons.

    Uses monoisotopic residue weights; subtracts water for each peptide bond.
    """
    seq = sequence.upper()
    if seq_type == "protein":
        weight = sum(AMINO_ACID_WEIGHTS.get(aa, 110.0) for aa in seq)
        # Subtract water for each peptide bond formed
        weight -= (len(seq) - 1) * 18.015
        return round(weight, 2)
    # DNA/RNA: average nucleotide weight ~330 Da
    weights = NUCLEOTIDE_WEIGHTS.get(seq_type, {})
    weight = sum(weights.get(nt, 330.0) for nt in seq)
    # Subtract water for phosphodiester bonds
    weight -= (len(seq) - 1) * 18.015
    return round(weight, 2)


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence."""
    complement_map = str.maketrans("ACGTN", "TGCAN")
    return sequence.upper().translate(complement_map)[::-1]


def transcribe(dna_sequence: str) -> str:
    """Transcribe a DNA sequence to RNA (T → U)."""
    return dna_sequence.upper().replace("T", "U")


def translate_codon(codon: str) -> str:
    """Translate a single codon to its single-letter amino acid code."""
    return CODON_TABLE.get(codon.upper(), "X")


def find_start_codons(sequence: str) -> list[int]:
    """Return 0-based positions of all ATG start codons."""
    seq = sequence.upper()
    return [i for i in range(0, len(seq) - 2) if seq[i : i + 3] == "ATG"]


def translate_sequence(sequence: str, table: Dict[str, str] | None = None) -> str:
    """
    Translate a DNA sequence to protein using the standard codon table.
    Translation stops at the first stop codon (*).
    """
    codon_tbl = table or CODON_TABLE
    seq = sequence.upper()
    protein_chars: list[str] = []
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i : i + 3]
        aa = codon_tbl.get(codon, "X")
        if aa == "*":
            break
        protein_chars.append(aa)
    return "".join(protein_chars)
