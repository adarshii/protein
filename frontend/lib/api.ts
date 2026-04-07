import axios from 'axios'
import type {
  SequenceAnalysisResult,
  MoleculeAnalysisResult,
  DTIPrediction,
  GenomicsResult,
  AlignmentResult,
  ORF,
  VariantAnnotation,
} from './types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ??
      err.response?.data?.message ??
      err.message ??
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// ── Sequence Analysis ────────────────────────────────────────────────────────

export async function analyzeSequence(
  sequence: string,
  sequenceType: string
): Promise<SequenceAnalysisResult> {
  const { data } = await api.post('/api/v1/sequence/analyze', {
    sequence,
    sequence_type: sequenceType,
  })
  return data
}

export async function findORFs(
  sequence: string,
  minLength = 100
): Promise<{ orfs: ORF[]; total: number }> {
  const { data } = await api.post('/api/v1/sequence/orfs', {
    sequence,
    min_length: minLength,
  })
  return data
}

export async function pairwiseAlignment(
  seq1: string,
  seq2: string,
  algorithm = 'needleman_wunsch'
): Promise<AlignmentResult> {
  const { data } = await api.post('/api/v1/sequence/alignment', {
    sequence1: seq1,
    sequence2: seq2,
    algorithm,
  })
  return data
}

// ── Molecule Analysis ────────────────────────────────────────────────────────

export async function analyzeMolecule(smiles: string): Promise<MoleculeAnalysisResult> {
  const { data } = await api.post('/api/v1/molecule/analyze', { smiles })
  return data
}

export async function computeDescriptors(
  smiles: string
): Promise<Record<string, number>> {
  const { data } = await api.post('/api/v1/molecule/descriptors', { smiles })
  return data
}

// ── ML Predictions ───────────────────────────────────────────────────────────

export async function predictDTI(
  drugSmiles: string,
  targetSequence: string
): Promise<DTIPrediction> {
  const { data } = await api.post('/api/v1/predict/dti', {
    drug_smiles: drugSmiles,
    target_sequence: targetSequence,
  })
  return data
}

export async function predictADMET(smiles: string) {
  const { data } = await api.post('/api/v1/predict/admet', { smiles })
  return data
}

// ── Genomics / Omics ─────────────────────────────────────────────────────────

export async function annotateVariant(
  chromosome: string,
  position: number,
  ref: string,
  alt: string
): Promise<VariantAnnotation> {
  const { data } = await api.post('/api/v1/genomics/variant', {
    chromosome,
    position,
    ref,
    alt,
  })
  return data
}

export async function annotateVariants(
  variants: Array<{ chromosome: string; position: number; ref: string; alt: string }>
): Promise<GenomicsResult> {
  const { data } = await api.post('/api/v1/genomics/variants/batch', { variants })
  return data
}

export async function getGeneExpression(geneIds: string[]) {
  const { data } = await api.post('/api/v1/omics/expression', { gene_ids: geneIds })
  return data
}

export async function pathwayEnrichment(geneList: string[]) {
  const { data } = await api.post('/api/v1/omics/pathway', { genes: geneList })
  return data
}

export default api
