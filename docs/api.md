# API Reference

## Base URL

| Environment | URL |
|---|---|
| Local development | `http://localhost:8000` |
| Production | `https://biochemai-api.onrender.com` |

Interactive docs are available at `{BASE_URL}/docs` (Swagger UI) and `{BASE_URL}/redoc`.

---

## Authentication

The API uses **JWT Bearer tokens**.

### Obtain a Token

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

**Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Use the Token

Include the token in the `Authorization` header for all protected endpoints:

```http
Authorization: Bearer <access_token>
```

---

## Bio Service (`/bio`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/bio/predict` | ✅ | Submit a protein structure prediction job |
| `GET` | `/bio/predict/{job_id}` | ✅ | Get prediction job status and result |
| `POST` | `/bio/blast` | ✅ | Run a BLAST sequence similarity search |
| `POST` | `/bio/align` | ✅ | Align two or more sequences |
| `GET` | `/bio/proteins/{accession}` | ❌ | Retrieve protein metadata by accession |

### Example: Submit Prediction

```http
POST /bio/predict
Authorization: Bearer <token>
Content-Type: application/json

{
  "sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGEDEDTFLSLQTEGDNPEEAGEGQLQ"
}
```

**Response**

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Chem Service (`/chem`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/chem/properties` | ❌ | Calculate molecular properties from SMILES |
| `POST` | `/chem/similarity` | ❌ | Compute Tanimoto similarity between molecules |
| `GET` | `/chem/molecules/{inchi_key}` | ❌ | Retrieve stored molecule by InChIKey |
| `POST` | `/chem/druglikeness` | ❌ | Score drug-likeness (Lipinski, QED) |
| `POST` | `/chem/substructure` | ❌ | Substructure search over the molecule database |

### Example: Calculate Properties

```http
POST /chem/properties
Content-Type: application/json

{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O"
}
```

**Response**

```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
  "molecular_weight": 180.16,
  "logp": 1.31,
  "hbd": 1,
  "hba": 4,
  "tpsa": 63.6,
  "rotatable_bonds": 3,
  "lipinski_pass": true,
  "qed": 0.55
}
```

---

## ML Service (`/ml`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/ml/models` | ❌ | List available ML models |
| `GET` | `/ml/models/{model_id}` | ❌ | Get model metadata |
| `POST` | `/ml/infer/{model_id}` | ✅ | Run inference with a registered model |
| `GET` | `/ml/infer/{job_id}` | ✅ | Get inference job status and result |

### Example: Run Inference

```http
POST /ml/infer/toxicity-v1
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": {
    "smiles": "CC(=O)Oc1ccccc1C(=O)O"
  }
}
```

**Response**

```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "model_id": "toxicity-v1",
  "status": "complete",
  "result": {
    "ld50_mg_kg": 200,
    "toxicity_class": "III",
    "confidence": 0.87
  }
}
```

---

## Genomics Service (`/genomics`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/genomics/analyze` | ✅ | Submit a sequence analysis job |
| `GET` | `/genomics/analyze/{job_id}` | ✅ | Get analysis job status and result |
| `GET` | `/genomics/sequences/{accession}` | ❌ | Fetch sequence record by accession |
| `POST` | `/genomics/variants` | ✅ | Annotate variants from a VCF payload |

### Example: Sequence Analysis

```http
POST /genomics/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "sequence": "ATGCGTACGTAGCTAGCTAGCTAGCTAGCTAG",
  "type": "dna",
  "analyses": ["gc_content", "orfs", "repeats"]
}
```

**Response**

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "complete",
  "result": {
    "gc_content": 0.53,
    "orfs": [],
    "repeats": [{"sequence": "AGCTAGCT", "count": 4, "positions": [6, 14, 22, 30]}]
  }
}
```

---

## Error Codes

| HTTP Status | Code | Description |
|---|---|---|
| 400 | `INVALID_INPUT` | Request body failed validation |
| 401 | `UNAUTHORIZED` | Missing or invalid JWT token |
| 403 | `FORBIDDEN` | Valid token but insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource already exists (e.g. duplicate molecule) |
| 422 | `UNPROCESSABLE_ENTITY` | Semantically invalid input (e.g. bad SMILES) |
| 429 | `RATE_LIMITED` | Too many requests; back off and retry |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Downstream dependency unavailable |

### Error Response Shape

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Field 'smiles' is not a valid SMILES string.",
    "details": {}
  }
}
```
