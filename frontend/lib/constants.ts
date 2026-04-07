import { SequenceType } from './types'

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const SEQUENCE_TYPES: { value: SequenceType; label: string }[] = [
  { value: SequenceType.DNA, label: 'DNA' },
  { value: SequenceType.RNA, label: 'RNA' },
  { value: SequenceType.PROTEIN, label: 'Protein' },
]

export const ALIGNMENT_ALGORITHMS = [
  { value: 'needleman_wunsch', label: 'Needleman-Wunsch (Global)' },
  { value: 'smith_waterman', label: 'Smith-Waterman (Local)' },
]

export const MAX_SEQUENCE_LENGTH = 50_000

export const MOLECULE_EXAMPLE_SMILES = [
  { label: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O' },
  { label: 'Ibuprofen', smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O' },
  { label: 'Caffeine', smiles: 'Cn1cnc2c1c(=O)n(c(=O)n2C)C' },
  { label: 'Paracetamol', smiles: 'CC(=O)Nc1ccc(O)cc1' },
]

export const DNA_EXAMPLE =
  'ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAGCGAGCGCCGAAATTTCCGGAGCTTCTGCAGGATCGATCCTTGCGCAGCGA'

export const PROTEIN_EXAMPLE =
  'MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY'

/** Interval in ms between job status poll requests. */
export const POLL_INTERVAL_MS = 2000
/** Maximum number of poll attempts before giving up (total wait ≈ 60 s). */
export const MAX_POLL_ATTEMPTS = 30
