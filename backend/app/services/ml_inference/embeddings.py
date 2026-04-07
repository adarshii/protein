"""Protein and drug embedding generators."""

from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional numpy
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NUMPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Protein embedder
# ---------------------------------------------------------------------------

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")
_AA_INDEX: Dict[str, int] = {aa: i for i, aa in enumerate(AMINO_ACIDS)}


class ProteinEmbedder:
    """Generate fixed-length numerical representations of protein sequences."""

    def encode(self, sequence: str, method: str = "kmer", k: int = 3) -> List[float]:
        """
        Encode a protein sequence as a flat embedding vector.

        Args:
            sequence: Single-letter amino-acid sequence.
            method: "kmer" for k-mer frequency, "onehot" for positional one-hot.
            k: k-mer length (used only with method="kmer").

        Returns:
            Flat list of floats.
        """
        seq = sequence.upper()
        if method == "kmer":
            return self._kmer_embedding(seq, k)
        if method == "onehot":
            return self._onehot_embedding(seq)
        raise ValueError(f"Unknown embedding method: {method}. Use 'kmer' or 'onehot'.")

    def batch_encode(
        self, sequences: List[str], method: str = "kmer", k: int = 3
    ) -> List[List[float]]:
        """Encode a list of protein sequences."""
        return [self.encode(seq, method, k) for seq in sequences]

    def _kmer_embedding(self, sequence: str, k: int) -> List[float]:
        """
        Compute normalised k-mer frequency vector.

        Dimension = 20^k (only canonical amino acids).
        """
        n_kmers = 20 ** k
        counts = [0.0] * n_kmers
        total = 0

        for i in range(len(sequence) - k + 1):
            kmer = sequence[i : i + k]
            if all(c in _AA_INDEX for c in kmer):
                idx = 0
                for c in kmer:
                    idx = idx * 20 + _AA_INDEX[c]
                if idx < n_kmers:
                    counts[idx] += 1
                    total += 1

        if total > 0:
            counts = [c / total for c in counts]
        return counts

    @staticmethod
    def _onehot_embedding(sequence: str, max_len: int = 512) -> List[float]:
        """
        One-hot encode sequence up to max_len residues.
        Pads with zeros if shorter; truncates if longer.
        Dimension = max_len * 20.
        """
        n_aa = len(AMINO_ACIDS)
        vector = [0.0] * (max_len * n_aa)
        for i, aa in enumerate(sequence[:max_len]):
            idx = _AA_INDEX.get(aa)
            if idx is not None:
                vector[i * n_aa + idx] = 1.0
        return vector


# ---------------------------------------------------------------------------
# Drug embedder
# ---------------------------------------------------------------------------


class DrugEmbedder:
    """Generate molecular fingerprint embeddings for small molecules."""

    def encode(self, smiles: str, fp_type: str = "morgan", n_bits: int = 2048) -> List[int]:
        """
        Compute a binary fingerprint bit vector for a SMILES string.

        Args:
            smiles: SMILES string.
            fp_type: "morgan" | "maccs" | "rdkit"
            n_bits: Number of bits (only for Morgan/RDKit).

        Returns:
            List of int (0 or 1), length = n_bits (or 167 for MACCS).
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import MACCSkeys, rdFingerprintGenerator
        except ImportError:
            logger.warning("rdkit_not_available_drug_embedder")
            return [0] * n_bits

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning("invalid_smiles", smiles=smiles)
            return [0] * n_bits

        fp_type = fp_type.lower()
        if fp_type == "morgan":
            gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=n_bits)
            fp = gen.GetFingerprint(mol)
        elif fp_type == "maccs":
            fp = MACCSkeys.GenMACCSKeys(mol)
        elif fp_type == "rdkit":
            gen = rdFingerprintGenerator.GetRDKitFPGenerator(fpSize=n_bits)
            fp = gen.GetFingerprint(mol)
        else:
            raise ValueError(f"Unknown fingerprint type: {fp_type}")

        return [int(b) for b in fp.ToBitString()]

    def batch_encode(
        self, smiles_list: List[str], fp_type: str = "morgan", n_bits: int = 2048
    ) -> List[List[int]]:
        """Encode a list of SMILES strings."""
        return [self.encode(smi, fp_type, n_bits) for smi in smiles_list]
