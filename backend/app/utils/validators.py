"""Input validation helpers."""

from __future__ import annotations

import re
from typing import Tuple

from app.utils.constants import AMINO_ACIDS, DNA_NUCLEOTIDES, RNA_NUCLEOTIDES

# ---------------------------------------------------------------------------
# Sequence validators
# ---------------------------------------------------------------------------

_DNA_RE = re.compile(r"^[ACGTN]+$", re.IGNORECASE)
_RNA_RE = re.compile(r"^[ACGUN]+$", re.IGNORECASE)
_PROTEIN_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYX*\-]+$", re.IGNORECASE)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
_SMILES_RE = re.compile(
    r"^[A-Za-z0-9@+\-\[\]()#=%\\/.,:*~]+$"
)


def validate_dna_sequence(seq: str) -> Tuple[bool, str]:
    """
    Validate that *seq* is a legal DNA sequence (ACGTN only).

    Returns:
        (is_valid, error_message) tuple.
    """
    if not seq:
        return False, "Sequence must not be empty."
    if len(seq) > 100_000:
        return False, "Sequence exceeds maximum length of 100,000 characters."
    if not _DNA_RE.match(seq):
        invalid = sorted({c for c in seq.upper() if c not in DNA_NUCLEOTIDES | {"N"}})
        return False, f"Invalid DNA characters: {', '.join(invalid)}"
    return True, ""


def validate_rna_sequence(seq: str) -> Tuple[bool, str]:
    """Validate that *seq* is a legal RNA sequence (ACGUN only)."""
    if not seq:
        return False, "Sequence must not be empty."
    if len(seq) > 100_000:
        return False, "Sequence exceeds maximum length of 100,000 characters."
    if not _RNA_RE.match(seq):
        invalid = sorted({c for c in seq.upper() if c not in RNA_NUCLEOTIDES | {"N"}})
        return False, f"Invalid RNA characters: {', '.join(invalid)}"
    return True, ""


def validate_protein_sequence(seq: str) -> Tuple[bool, str]:
    """Validate that *seq* is a legal single-letter protein sequence."""
    if not seq:
        return False, "Sequence must not be empty."
    if len(seq) > 100_000:
        return False, "Sequence exceeds maximum length of 100,000 characters."
    if not _PROTEIN_RE.match(seq):
        invalid = sorted(
            {c for c in seq.upper() if c not in AMINO_ACIDS | {"X", "*", "-"}}
        )
        return False, f"Invalid protein characters: {', '.join(invalid)}"
    return True, ""


def validate_smiles(smiles: str) -> Tuple[bool, str]:
    """
    Basic SMILES validation using character set check.

    For full chemical validation, use RDKit's ``Chem.MolFromSmiles``.
    """
    if not smiles:
        return False, "SMILES must not be empty."
    if len(smiles) > 10_000:
        return False, "SMILES exceeds maximum length of 10,000 characters."
    if not _SMILES_RE.match(smiles):
        return False, "SMILES contains illegal characters."
    # Basic bracket balance check
    if smiles.count("[") != smiles.count("]"):
        return False, "Unbalanced square brackets in SMILES."
    if smiles.count("(") != smiles.count(")"):
        return False, "Unbalanced parentheses in SMILES."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate an email address using a simple regex."""
    if not _EMAIL_RE.match(email):
        return False, f"'{email}' is not a valid email address."
    return True, ""


# ---------------------------------------------------------------------------
# Sanitisation
# ---------------------------------------------------------------------------

_XSS_TAGS = re.compile(r"<[^>]*>", re.IGNORECASE)
_SQL_COMMENTS = re.compile(r"(--|;|/\*|\*/)", re.IGNORECASE)
_NULL_BYTES = re.compile(r"\x00")


def sanitize_input(text: str, max_length: int = 10_000) -> str:
    """
    Remove potentially dangerous patterns from free-text input.

    Strips HTML/XML tags, SQL comment patterns, and null bytes.
    Truncates to *max_length* characters.

    Args:
        text: Raw user input.
        max_length: Maximum length to allow.

    Returns:
        Sanitised string.
    """
    text = _NULL_BYTES.sub("", text)
    text = _XSS_TAGS.sub("", text)
    text = _SQL_COMMENTS.sub("", text)
    return text[:max_length]
