import { create } from 'zustand'
import type {
  SequenceAnalysisResult,
  MoleculeAnalysisResult,
  MLPredictionResult,
  JobStatus,
} from '@/lib/types'

interface SequenceEntry {
  id: string
  sequence: string
  sequenceType: string
  result?: SequenceAnalysisResult
  timestamp: number
}

interface MoleculeEntry {
  id: string
  smiles: string
  result?: MoleculeAnalysisResult
  timestamp: number
}

interface AnalysisStore {
  // State
  sequences: SequenceEntry[]
  molecules: MoleculeEntry[]
  predictions: MLPredictionResult[]
  sequenceStatus: JobStatus
  moleculeStatus: JobStatus
  sequenceError: string | null
  moleculeError: string | null
  activeSequenceId: string | null
  activeMoleculeId: string | null

  // Actions
  addSequence: (entry: Omit<SequenceEntry, 'id' | 'timestamp'>) => string
  updateSequenceResult: (id: string, result: SequenceAnalysisResult) => void
  addMolecule: (entry: Omit<MoleculeEntry, 'id' | 'timestamp'>) => string
  updateMoleculeResult: (id: string, result: MoleculeAnalysisResult) => void
  addPrediction: (prediction: MLPredictionResult) => void
  setSequenceStatus: (status: JobStatus, error?: string) => void
  setMoleculeStatus: (status: JobStatus, error?: string) => void
  setActiveSequence: (id: string | null) => void
  setActiveMolecule: (id: string | null) => void
  clearAll: () => void
}

let _id = 0
const nextId = () => `entry-${++_id}-${Date.now()}`

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  sequences: [],
  molecules: [],
  predictions: [],
  sequenceStatus: 'idle',
  moleculeStatus: 'idle',
  sequenceError: null,
  moleculeError: null,
  activeSequenceId: null,
  activeMoleculeId: null,

  addSequence: (entry) => {
    const id = nextId()
    set((s) => ({
      sequences: [{ ...entry, id, timestamp: Date.now() }, ...s.sequences].slice(0, 20),
      activeSequenceId: id,
    }))
    return id
  },

  updateSequenceResult: (id, result) =>
    set((s) => ({
      sequences: s.sequences.map((e) => (e.id === id ? { ...e, result } : e)),
    })),

  addMolecule: (entry) => {
    const id = nextId()
    set((s) => ({
      molecules: [{ ...entry, id, timestamp: Date.now() }, ...s.molecules].slice(0, 20),
      activeMoleculeId: id,
    }))
    return id
  },

  updateMoleculeResult: (id, result) =>
    set((s) => ({
      molecules: s.molecules.map((e) => (e.id === id ? { ...e, result } : e)),
    })),

  addPrediction: (prediction) =>
    set((s) => ({ predictions: [prediction, ...s.predictions].slice(0, 50) })),

  setSequenceStatus: (status, error) =>
    set({ sequenceStatus: status, sequenceError: error ?? null }),

  setMoleculeStatus: (status, error) =>
    set({ moleculeStatus: status, moleculeError: error ?? null }),

  setActiveSequence: (id) => set({ activeSequenceId: id }),
  setActiveMolecule: (id) => set({ activeMoleculeId: id }),

  clearAll: () =>
    set({
      sequences: [],
      molecules: [],
      predictions: [],
      sequenceStatus: 'idle',
      moleculeStatus: 'idle',
      sequenceError: null,
      moleculeError: null,
      activeSequenceId: null,
      activeMoleculeId: null,
    }),
}))
