"""Application-wide constants."""

from __future__ import annotations

from typing import Dict, Set

# ---------------------------------------------------------------------------
# Version / API
# ---------------------------------------------------------------------------

API_VERSION: str = "v1"
APP_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Sequence constraints
# ---------------------------------------------------------------------------

MAX_SEQUENCE_LENGTH: int = 100_000
MIN_ORF_LENGTH: int = 100
DEFAULT_CACHE_TTL: int = 3600  # seconds

# ---------------------------------------------------------------------------
# Nucleotide / amino-acid character sets
# ---------------------------------------------------------------------------

DNA_NUCLEOTIDES: Set[str] = {"A", "C", "G", "T", "N"}
RNA_NUCLEOTIDES: Set[str] = {"A", "C", "G", "U", "N"}
AMINO_ACIDS: Set[str] = set("ACDEFGHIKLMNPQRSTVWY")

# ---------------------------------------------------------------------------
# Supported algorithms
# ---------------------------------------------------------------------------

SUPPORTED_ALIGNMENT_ALGORITHMS: list[str] = ["needleman_wunsch", "smith_waterman"]
SUPPORTED_FINGERPRINT_TYPES: list[str] = ["morgan", "maccs", "rdkit"]
SUPPORTED_EMBEDDING_METHODS: list[str] = ["kmer", "onehot"]

# ---------------------------------------------------------------------------
# Molecular weights (Da) — amino acid residue weights (monoisotopic)
# ---------------------------------------------------------------------------

AMINO_ACID_WEIGHTS: Dict[str, float] = {
    "A": 89.047_68,
    "C": 121.019_75,
    "D": 133.037_64,
    "E": 147.053_29,
    "F": 165.079_04,
    "G": 75.032_03,
    "H": 155.069_48,
    "I": 131.094_63,
    "K": 146.105_53,
    "L": 131.094_63,
    "M": 149.051_05,
    "N": 132.053_49,
    "P": 115.063_33,
    "Q": 146.069_14,
    "R": 174.111_68,
    "S": 105.042_59,
    "T": 119.058_24,
    "V": 117.078_98,
    "W": 204.089_88,
    "Y": 181.073_97,
}

# Average nucleotide residue weights (Da) — approximate
NUCLEOTIDE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "dna": {"A": 331.2, "C": 307.2, "G": 347.2, "T": 322.2, "N": 327.0},
    "rna": {"A": 347.2, "C": 323.2, "G": 363.2, "U": 324.2, "N": 339.5},
}

# ---------------------------------------------------------------------------
# Standard genetic code — codon table (NCBI table 1)
# ---------------------------------------------------------------------------

CODON_TABLE: Dict[str, str] = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

# ---------------------------------------------------------------------------
# HTTP / external services
# ---------------------------------------------------------------------------

UNIPROT_FIELDS: list[str] = [
    "accession",
    "gene_names",
    "protein_name",
    "organism_name",
    "sequence",
    "function",
]

PUBCHEM_PROPERTIES: list[str] = [
    "MolecularFormula",
    "MolecularWeight",
    "IUPACName",
    "IsomericSMILES",
    "InChI",
    "InChIKey",
    "XLogP",
    "TPSA",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
]
