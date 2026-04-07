export enum SequenceType {
  DNA = 'DNA',
  RNA = 'RNA',
  PROTEIN = 'PROTEIN',
}

export interface SequenceAnalysisResult {
  sequence_type: SequenceType
  length: number
  gc_content?: number
  at_content?: number
  composition: Record<string, number>
  molecular_weight?: number
  orfs?: ORF[]
  alignment?: AlignmentResult
  error?: string
}

export interface ORF {
  start: number
  end: number
  strand: '+' | '-'
  frame: number
  length: number
  sequence: string
}

export interface AlignmentResult {
  score: number
  identity: number
  gaps: number
  aligned_seq1: string
  aligned_seq2: string
}

export interface MoleculeAnalysisResult {
  smiles: string
  molecular_weight: number
  logp: number
  hbd: number
  hba: number
  tpsa: number
  rotatable_bonds: number
  rings: number
  lipinski_passes: boolean
  descriptors: Record<string, number>
  error?: string
}

export interface MLPredictionResult {
  prediction: number | string
  probability?: number
  confidence?: number
  explanation?: SHAPExplanation
  model_name: string
  model_version?: string
}

export interface SHAPExplanation {
  feature_names: string[]
  shap_values: number[]
  base_value: number
  expected_value: number
}

export interface DTIPrediction {
  drug_smiles: string
  target_sequence: string
  binding_probability: number
  binding_affinity?: number
  confidence: string
  explanation?: SHAPExplanation
}

export interface ADMETProperties {
  absorption: {
    bioavailability: number
    intestinal_absorption: number
    pgp_substrate: boolean
  }
  distribution: {
    vd: number
    bbb_permeant: boolean
    ppb: number
  }
  metabolism: {
    cyp1a2_inhibitor: boolean
    cyp3a4_inhibitor: boolean
    cyp2d6_inhibitor: boolean
  }
  excretion: {
    half_life: number
    clearance: number
  }
  toxicity: {
    ames_toxic: boolean
    herg_inhibitor: boolean
    ld50: number
  }
}

export interface VariantAnnotation {
  chromosome: string
  position: number
  ref: string
  alt: string
  gene?: string
  consequence?: string
  clinical_significance?: string
  frequency?: number
  rsid?: string
}

export interface GenomicsResult {
  variants: VariantAnnotation[]
  total: number
  error?: string
}

export interface PathwayResult {
  pathway_id: string
  pathway_name: string
  gene_count: number
  p_value: number
  fdr: number
  genes: string[]
}

export interface ApiError {
  message: string
  status: number
  detail?: string
}

export type JobStatus = 'idle' | 'loading' | 'success' | 'error'

export interface Job {
  id: string
  type: string
  status: JobStatus
  created_at: string
  result?: unknown
  error?: string
}
