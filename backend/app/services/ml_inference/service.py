"""ML inference service — DTI, toxicity, and explainability."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import structlog

from app.services.ml_inference.embeddings import DrugEmbedder, ProteinEmbedder

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional scikit-learn / numpy
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _NUMPY = True
except ImportError:  # pragma: no cover
    _NUMPY = False


class MLInferenceService:
    """
    ML inference service providing drug-target interaction prediction,
    toxicity estimation, and prediction explanation.

    All models in this reference implementation use rule-based heuristics
    and embedding-derived features. In production these would be replaced
    with trained neural-network or gradient-boosted models.
    """

    def __init__(self) -> None:
        self._prot_embedder = ProteinEmbedder()
        self._drug_embedder = DrugEmbedder()

    # ------------------------------------------------------------------
    # Drug-target interaction
    # ------------------------------------------------------------------

    async def predict_dti(
        self, protein_sequence: str, smiles: str
    ) -> Dict[str, Any]:
        """
        Predict whether a small molecule binds to the given protein.

        Uses k-mer protein embedding + Morgan fingerprint, then computes a
        cosine-similarity-like heuristic score.

        Args:
            protein_sequence: Amino-acid sequence.
            smiles: SMILES string of the drug candidate.

        Returns:
            dict with interaction_probability, confidence, and feature importances.
        """
        prot_emb = self._prot_embedder.encode(protein_sequence, method="kmer", k=2)
        drug_emb = self._drug_embedder.encode(smiles, fp_type="morgan", n_bits=512)

        # Simple heuristic: normalised dot product between non-zero features
        prot_sum = sum(prot_emb)
        drug_on = sum(drug_emb)
        drug_total = len(drug_emb)

        # Proxy score derived from embedding statistics
        if prot_sum > 0 and drug_total > 0:
            diversity = drug_on / drug_total
            prot_entropy = self._entropy(prot_emb)
            raw_score = 0.4 * diversity + 0.6 * min(prot_entropy / 4.0, 1.0)
        else:
            raw_score = 0.0

        probability = round(min(max(raw_score, 0.0), 1.0), 4)

        return {
            "protein_length": len(protein_sequence),
            "smiles": smiles,
            "interaction_probability": probability,
            "predicted_class": "binder" if probability >= 0.5 else "non-binder",
            "confidence": round(abs(probability - 0.5) * 2, 4),
            "feature_importances": {
                "drug_diversity": round(drug_on / drug_total if drug_total else 0, 4),
                "protein_entropy": round(self._entropy(prot_emb), 4),
            },
            "model": "heuristic_v1",
        }

    # ------------------------------------------------------------------
    # Toxicity prediction
    # ------------------------------------------------------------------

    async def predict_toxicity(
        self, smiles: str, models: List[str]
    ) -> Dict[str, Any]:
        """
        Predict multi-endpoint toxicity for a molecule.

        Uses molecular descriptor rules as proxies for trained classifiers.

        Args:
            smiles: SMILES string.
            models: List of endpoints to predict (ames, herg, hepatotoxicity).

        Returns:
            dict mapping each endpoint to a probability and class.
        """
        results: Dict[str, Any] = {"smiles": smiles, "endpoints": {}}

        # Fetch descriptors if RDKit is available
        descriptors: Dict[str, float] = {}
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, rdMolDescriptors
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                descriptors = {
                    "mw": Descriptors.ExactMolWt(mol),
                    "logp": Descriptors.MolLogP(mol),
                    "hbd": rdMolDescriptors.CalcNumHBD(mol),
                    "hba": rdMolDescriptors.CalcNumHBA(mol),
                    "tpsa": float(rdMolDescriptors.CalcTPSA(mol)),
                    "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
                    "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
                }
        except ImportError:
            pass

        for endpoint in models:
            prob = self._endpoint_probability(endpoint, descriptors)
            results["endpoints"][endpoint] = {
                "probability": round(prob, 4),
                "predicted_class": "toxic" if prob >= 0.5 else "non-toxic",
                "confidence": round(abs(prob - 0.5) * 2, 4),
            }

        results["overall_safety_score"] = round(
            1.0 - (
                sum(ep["probability"] for ep in results["endpoints"].values())
                / max(len(results["endpoints"]), 1)
            ),
            4,
        )
        return results

    @staticmethod
    def _endpoint_probability(endpoint: str, desc: Dict[str, float]) -> float:
        """Rule-based proxy probability for a toxicity endpoint."""
        if not desc:
            return 0.5

        mw = desc.get("mw", 300.0)
        logp = desc.get("logp", 1.0)
        aromatic_rings = desc.get("aromatic_rings", 0)
        hbd = desc.get("hbd", 0)

        if endpoint == "ames":
            # Mutagenicity correlated with aromatic amines / planar structures
            score = 0.1 + 0.15 * aromatic_rings + 0.05 * (logp > 3)
            return min(score, 0.95)
        if endpoint == "herg":
            # hERG inhibition: high logP and high MW increase risk
            score = 0.05 + 0.01 * max(logp - 1, 0) + 0.0005 * max(mw - 300, 0)
            return min(score, 0.95)
        if endpoint == "hepatotoxicity":
            score = 0.1 + 0.02 * (logp > 4) * logp + 0.01 * (hbd > 5)
            return min(score, 0.95)
        return 0.5

    # ------------------------------------------------------------------
    # SHAP-style explanation
    # ------------------------------------------------------------------

    async def explain_prediction(
        self,
        features: Dict[str, float],
        prediction: float,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Compute simplified SHAP-like feature importances using leave-one-out
        sensitivity analysis around the mean baseline.

        Args:
            features: Feature name → value mapping.
            prediction: The model's prediction to explain.
            top_k: Number of top features to return.

        Returns:
            dict with sorted feature importances and summary statistics.
        """
        if not features:
            return {"importances": [], "baseline": 0.5}

        values = list(features.values())
        mean_val = sum(values) / len(values)
        std_val = math.sqrt(
            sum((v - mean_val) ** 2 for v in values) / len(values)
        ) or 1.0

        importances = []
        for name, val in features.items():
            # Scaled deviation from mean as proxy for SHAP value
            shap_val = (val - mean_val) / std_val * prediction * 0.1
            importances.append({"feature": name, "shap_value": round(shap_val, 6), "value": val})

        importances.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        return {
            "prediction": prediction,
            "baseline": round(mean_val, 4),
            "top_features": importances[:top_k],
            "n_features": len(features),
            "method": "leave_one_out_heuristic",
        }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _entropy(probabilities: List[float]) -> float:
        """Compute Shannon entropy of a probability distribution."""
        total = sum(probabilities)
        if total == 0:
            return 0.0
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                pn = p / total
                entropy -= pn * math.log2(pn)
        return entropy
