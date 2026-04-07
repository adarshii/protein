"""Genomics service — variant annotation, SNP analysis, pathway enrichment."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, TypedDict

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Reference data stubs
# These would be backed by real databases (ClinVar, gnomAD, KEGG/Reactome)
# in a production deployment.
# ---------------------------------------------------------------------------

_VARIANT_CONSEQUENCES = [
    "missense_variant",
    "synonymous_variant",
    "stop_gained",
    "frameshift_variant",
    "splice_site_variant",
    "intron_variant",
    "upstream_gene_variant",
    "intergenic_variant",
]

_CLINICAL_SIGNIFICANCE = [
    "benign",
    "likely_benign",
    "uncertain_significance",
    "likely_pathogenic",
    "pathogenic",
]

class _PathwayEntry(TypedDict):
    name: str
    genes: List[str]


_PATHWAY_DB: Dict[str, _PathwayEntry] = {
    "KEGG:hsa04010": {
        "name": "MAPK signaling pathway",
        "genes": ["MAPK1", "MAPK3", "RAF1", "MAP2K1", "MAP2K2", "KRAS", "HRAS", "NRAS"],
    },
    "KEGG:hsa04151": {
        "name": "PI3K-Akt signaling pathway",
        "genes": ["AKT1", "AKT2", "PIK3CA", "PIK3R1", "PTEN", "MTOR"],
    },
    "KEGG:hsa04110": {
        "name": "Cell cycle",
        "genes": ["CDK1", "CDK2", "CDK4", "CDK6", "CCND1", "CCNE1", "RB1", "TP53"],
    },
    "REACTOME:R-HSA-9612973": {
        "name": "Autophagy",
        "genes": ["ATG5", "ATG7", "ATG12", "BECN1", "ULK1", "MTOR"],
    },
    "KEGG:hsa04115": {
        "name": "p53 signaling pathway",
        "genes": ["TP53", "MDM2", "CDKN1A", "BAX", "BCL2", "CASP3"],
    },
}

_GENE_DB: Dict[str, Dict[str, Any]] = {
    "TP53": {
        "ensembl_id": "ENSG00000141510",
        "chromosome": "chr17",
        "start": 7_661_779,
        "end": 7_687_538,
        "strand": "-",
        "biotype": "protein_coding",
        "description": "Tumor protein p53",
        "omim": "191170",
    },
    "BRCA1": {
        "ensembl_id": "ENSG00000012048",
        "chromosome": "chr17",
        "start": 43_044_295,
        "end": 43_170_245,
        "strand": "-",
        "biotype": "protein_coding",
        "description": "BRCA1 DNA repair associated",
        "omim": "113705",
    },
    "KRAS": {
        "ensembl_id": "ENSG00000133703",
        "chromosome": "chr12",
        "start": 25_204_789,
        "end": 25_250_929,
        "strand": "-",
        "biotype": "protein_coding",
        "description": "KRAS proto-oncogene, GTPase",
        "omim": "190070",
    },
}


class GenomicsService:
    """Service layer for genomics operations."""

    # ------------------------------------------------------------------
    # Variant annotation
    # ------------------------------------------------------------------

    async def annotate_variant(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        genome_build: str = "GRCh38",
    ) -> Dict[str, Any]:
        """
        Annotate a genomic variant with predicted functional consequences.

        In production this would query VEP (Variant Effect Predictor),
        ClinVar, and gnomAD. Here we return a structured mock response.

        Args:
            chrom: Chromosome identifier.
            pos: 1-based genomic position.
            ref: Reference allele.
            alt: Alternate allele.
            genome_build: Reference genome (GRCh37 or GRCh38).

        Returns:
            Structured annotation dict.
        """
        variant_type = self._classify_variant(ref, alt)
        rng = random.Random(f"{chrom}:{pos}:{ref}:{alt}")
        consequence = rng.choice(_VARIANT_CONSEQUENCES)
        clin_sig = rng.choice(_CLINICAL_SIGNIFICANCE)
        gnomad_af = rng.uniform(0, 0.05)

        return {
            "variant": f"{chrom}:{pos}:{ref}>{alt}",
            "genome_build": genome_build,
            "variant_type": variant_type,
            "consequence": consequence,
            "impact": self._consequence_impact(consequence),
            "clinical_significance": clin_sig,
            "population_frequencies": {
                "gnomad_af": round(gnomad_af, 6),
                "gnomad_af_eas": round(gnomad_af * rng.uniform(0.5, 2), 6),
                "gnomad_af_afr": round(gnomad_af * rng.uniform(0.5, 2), 6),
            },
            "in_silico_predictions": {
                "sift": rng.choice(["tolerated", "deleterious"]),
                "polyphen2": rng.choice(["benign", "possibly_damaging", "probably_damaging"]),
                "cadd_phred": round(rng.uniform(1, 40), 2),
            },
            "note": "Mock annotation. Connect to VEP/ClinVar/gnomAD in production.",
        }

    @staticmethod
    def _classify_variant(ref: str, alt: str) -> str:
        if len(ref) == len(alt) == 1:
            return "SNV"
        if len(ref) > len(alt):
            return "deletion"
        if len(ref) < len(alt):
            return "insertion"
        return "MNV"

    @staticmethod
    def _consequence_impact(consequence: str) -> str:
        high = {"stop_gained", "frameshift_variant", "splice_site_variant"}
        moderate = {"missense_variant"}
        if consequence in high:
            return "HIGH"
        if consequence in moderate:
            return "MODERATE"
        return "LOW"

    # ------------------------------------------------------------------
    # SNP analysis
    # ------------------------------------------------------------------

    async def analyze_snp(self, rsid: str) -> Dict[str, Any]:
        """
        Retrieve allele frequency and functional annotation for a dbSNP variant.

        Args:
            rsid: dbSNP rsID string (e.g. "rs1234567").

        Returns:
            Structured SNP annotation dict.
        """
        rng = random.Random(rsid)
        alleles = rng.choice([("A", "G"), ("C", "T"), ("A", "C"), ("G", "T")])
        ref_freq = rng.uniform(0.4, 0.9)
        alt_freq = round(1 - ref_freq, 4)

        return {
            "rsid": rsid,
            "chromosome": f"chr{rng.randint(1, 22)}",
            "position": rng.randint(1_000_000, 200_000_000),
            "ref_allele": alleles[0],
            "alt_allele": alleles[1],
            "allele_frequencies": {
                "ref": round(ref_freq, 4),
                "alt": round(alt_freq, 4),
            },
            "clinical_significance": rng.choice(_CLINICAL_SIGNIFICANCE),
            "associated_genes": [],
            "note": "Mock SNP data. Integrate with dbSNP REST API for production.",
        }

    # ------------------------------------------------------------------
    # Gene info
    # ------------------------------------------------------------------

    async def get_gene_info(
        self, gene_id: str, include_transcripts: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve information about a gene by HGNC symbol or Ensembl ID.

        Args:
            gene_id: HGNC symbol (e.g. "TP53") or Ensembl gene ID.
            include_transcripts: If True, include transcript list.

        Returns:
            Gene annotation dict.
        """
        symbol = gene_id.upper()
        data = _GENE_DB.get(symbol)
        if data is None:
            # Return a minimal stub for unknown genes
            data = {
                "ensembl_id": f"ENSG{abs(hash(gene_id)) % 100_000_000_000:011d}",
                "chromosome": "unknown",
                "start": 0,
                "end": 0,
                "strand": "+",
                "biotype": "unknown",
                "description": f"Gene {gene_id} (not in local reference)",
                "omim": None,
            }

        result: Dict[str, Any] = {
            "symbol": symbol,
            **data,
        }

        if include_transcripts:
            rng = random.Random(gene_id)
            result["transcripts"] = [
                {
                    "transcript_id": f"ENST{rng.randint(0, 99999999999):011d}",
                    "length_bp": rng.randint(1000, 8000),
                    "biotype": "protein_coding",
                }
                for _ in range(rng.randint(2, 6))
            ]

        return result

    # ------------------------------------------------------------------
    # Pathway enrichment
    # ------------------------------------------------------------------

    async def pathway_enrichment(
        self,
        gene_list: List[str],
        background_size: int = 20_000,
        p_value_threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Perform over-representation analysis against a built-in pathway reference.

        Uses Fisher's exact test (one-sided) to compute p-values, then applies
        Benjamini-Hochberg FDR correction.

        Args:
            gene_list: List of HGNC gene symbols to test.
            background_size: Size of the background gene universe.
            p_value_threshold: Significance threshold (FDR-adjusted).

        Returns:
            dict with enriched pathways and statistics.
        """
        gene_set = {g.upper() for g in gene_list}
        n_query = len(gene_set)
        results = []

        for pathway_id, pathway_info in _PATHWAY_DB.items():
            pathway_genes = {g.upper() for g in pathway_info["genes"]}
            overlap = gene_set & pathway_genes

            if not overlap:
                continue

            k = len(overlap)  # successes in sample
            K = len(pathway_genes)  # successes in population
            n = n_query  # sample size
            N = background_size  # population size

            pval = self._hypergeometric_pvalue(k, K, n, N)
            results.append(
                {
                    "pathway_id": pathway_id,
                    "pathway_name": pathway_info["name"],
                    "overlap_genes": sorted(overlap),
                    "overlap_count": k,
                    "pathway_gene_count": K,
                    "query_gene_count": n_query,
                    "p_value": round(pval, 6),
                    "fold_enrichment": round(
                        (k / n) / (K / N) if K > 0 and n > 0 else 0.0, 3
                    ),
                }
            )

        # BH FDR correction
        results.sort(key=lambda x: x["p_value"])
        n_tests = len(results)
        for rank, res in enumerate(results, start=1):
            res["adjusted_p_value"] = round(
                min(res["p_value"] * n_tests / rank, 1.0), 6
            )

        significant = [r for r in results if r["adjusted_p_value"] <= p_value_threshold]

        return {
            "gene_list_size": n_query,
            "pathways_tested": n_tests,
            "significant_pathways": len(significant),
            "p_value_threshold": p_value_threshold,
            "results": results,
        }

    @staticmethod
    def _hypergeometric_pvalue(k: int, K: int, n: int, N: int) -> float:
        """
        Compute upper-tail hypergeometric p-value P(X >= k).

        Parameters follow scipy.stats.hypergeom convention:
            N = population size, K = successes in population,
            n = sample size, k = successes in sample.
        """
        try:
            from scipy.stats import hypergeom
            return float(hypergeom.sf(k - 1, N, K, n))
        except ImportError:
            pass

        # Fallback: log-sum approximation
        def log_comb(a: int, b: int) -> float:
            if b < 0 or b > a:
                return float("-inf")
            result = 0.0
            for i in range(b):
                result += math.log(a - i) - math.log(i + 1)
            return result

        log_total = log_comb(N, n)
        pval = 0.0
        for x in range(k, min(K, n) + 1):
            log_p = log_comb(K, x) + log_comb(N - K, n - x) - log_total
            pval += math.exp(log_p)
        return min(pval, 1.0)
