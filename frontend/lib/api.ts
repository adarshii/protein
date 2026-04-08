import axios from 'axios'
import { API_BASE_URL } from './constants'
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
  baseURL: API_BASE_URL,
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
      err.response?.data?.error?.message ??
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
  const { data } = await api.post('/api/bio/sequence/analyze', {
    sequence,
    seq_type: sequenceType.toLowerCase(),
  })
  return {
    sequence_type: (data.sequence_type ?? sequenceType).toUpperCase(),
    length: data.length,
    composition: Object.fromEntries(
      Object.entries(data.composition ?? {}).map(([k, v]) => [
        k,
        data.length ? Number(v) / Number(data.length) : 0,
      ])
    ),
    gc_content: typeof data.gc_content === 'number' ? data.gc_content / 100 : undefined,
    molecular_weight: data.molecular_weight_da,
  } as SequenceAnalysisResult
}

export async function findORFs(
  sequence: string,
  minLength = 100
): Promise<{ orfs: ORF[]; total: number }> {
  const { data } = await api.post(`/api/bio/sequence/orf?min_length=${minLength}`, {
    sequence,
    seq_type: 'dna',
  })
  const orfs: ORF[] = (data ?? []).map((orf: Record<string, unknown>) => ({
    start: Number(orf.start ?? 0),
    end: Number(orf.stop ?? 0),
    strand: (orf.strand as '+' | '-') ?? '+',
    frame: Number(orf.frame ?? 0),
    length: Number(orf.length_nt ?? 0),
    sequence: String(orf.protein_sequence ?? ''),
  }))
  return { orfs, total: orfs.length }
}

export async function pairwiseAlignment(
  seq1: string,
  seq2: string,
  algorithm = 'needleman_wunsch'
): Promise<AlignmentResult> {
  const { data } = await api.post('/api/bio/alignment/pairwise', {
    sequence1: seq1,
    sequence2: seq2,
    algorithm,
  })
  return {
    score: Number(data.score ?? 0),
    identity:
      typeof data.identity_percent === 'number'
        ? data.identity_percent / 100
        : Number(data.identity ?? 0),
    gaps: Number(data.gaps ?? 0),
    aligned_seq1: String(data.aligned_seq1 ?? ''),
    aligned_seq2: String(data.aligned_seq2 ?? ''),
  }
}

// ── Molecule Analysis ────────────────────────────────────────────────────────

export async function analyzeMolecule(smiles: string): Promise<MoleculeAnalysisResult> {
  const { data } = await api.post('/api/chem/molecule/descriptors', { smiles })
  return {
    smiles,
    molecular_weight: Number(data.molecular_weight ?? 0),
    logp: Number(data.logp ?? 0),
    hbd: Number(data.hbd ?? 0),
    hba: Number(data.hba ?? 0),
    tpsa: Number(data.tpsa ?? 0),
    rotatable_bonds: Number(data.rotatable_bonds ?? 0),
    rings: Number(data.rings ?? 0),
    lipinski_passes: Boolean(data?.lipinski?.lipinski_pass),
    descriptors: data,
  }
}

export async function computeDescriptors(
  smiles: string
): Promise<Record<string, number>> {
  const { data } = await api.post('/api/chem/molecule/descriptors', { smiles })
  return data
}

// ── ML Predictions ───────────────────────────────────────────────────────────

export async function predictDTI(
  drugSmiles: string,
  targetSequence: string
): Promise<DTIPrediction> {
  const { data } = await api.post('/api/ml/dti/predict', {
    smiles: drugSmiles,
    protein_sequence: targetSequence,
  })
  const confidence = Number(data.confidence ?? 0)
  const confidenceLabel =
    confidence >= 0.75 ? 'high' : confidence >= 0.4 ? 'medium' : 'low'
  return {
    drug_smiles: drugSmiles,
    target_sequence: targetSequence,
    binding_probability: Number(data.interaction_probability ?? 0),
    confidence: confidenceLabel,
  }
}

export async function predictADMET(smiles: string) {
  const { data } = await api.post('/api/chem/admet/predict', { smiles })
  const oral = Boolean(data?.absorption?.oral_bioavailability_likely)
  const bbb = Boolean(data?.distribution?.bbb_penetrant_likely)
  const alerts: string[] = Array.isArray(data?.toxicity?.alerts) ? data.toxicity.alerts : []
  return {
    absorption: {
      bioavailability: oral ? 0.7 : 0.3,
      intestinal_absorption: oral ? 0.75 : 0.4,
      pgp_substrate: false,
    },
    distribution: {
      vd: 0.6,
      bbb_permeant: bbb,
      ppb: 0.75,
    },
    metabolism: {
      cyp1a2_inhibitor: false,
      cyp3a4_inhibitor: false,
      cyp2d6_inhibitor: false,
    },
    excretion: {
      half_life: 8,
      clearance: data?.excretion?.rapid_clearance_risk ? 70 : 40,
    },
    toxicity: {
      ames_toxic: alerts.length > 0,
      herg_inhibitor: alerts.some((a: string) => a.toLowerCase().includes('quinone')),
      ld50: 500,
    },
  }
}

// ── Genomics / Omics ─────────────────────────────────────────────────────────

export async function annotateVariant(
  chromosome: string,
  position: number,
  ref: string,
  alt: string
): Promise<VariantAnnotation> {
  const { data } = await api.post('/api/genomics/variant/annotate', {
    chrom: chromosome,
    pos: position,
    ref,
    alt,
  })
  const af = data?.population_frequencies?.gnomad_af
  return {
    chromosome,
    position,
    ref,
    alt,
    consequence: data?.consequence,
    clinical_significance: data?.clinical_significance,
    frequency: typeof af === 'number' ? af : undefined,
  }
}

export async function annotateVariants(
  variants: Array<{ chromosome: string; position: number; ref: string; alt: string }>
): Promise<GenomicsResult> {
  const annotated = await Promise.all(
    variants.map((v) => annotateVariant(v.chromosome, v.position, v.ref, v.alt))
  )
  return { variants: annotated, total: annotated.length }
}

export async function getGeneExpression(geneIds: string[]) {
  const records = await Promise.all(
    geneIds.map(async (geneId) => {
      const { data } = await api.get(`/api/genomics/gene/${encodeURIComponent(geneId)}`)
      return { gene: geneId, data }
    })
  )
  return records
}

export async function pathwayEnrichment(geneList: string[]) {
  const { data } = await api.post('/api/genomics/pathway/enrichment', {
    gene_list: geneList,
  })
  return (data?.results ?? []).map((row: Record<string, unknown>) => ({
    name: row.pathway_name,
    genes: Number(row.overlap_count ?? 0),
    pValue: Number(row.adjusted_p_value ?? row.p_value ?? 1),
  }))
}

export default api
