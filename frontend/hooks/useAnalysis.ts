'use client'

import { useState, useCallback } from 'react'
import { analyzeSequence, analyzeMolecule } from '@/lib/api'
import type { SequenceAnalysisResult, MoleculeAnalysisResult, JobStatus } from '@/lib/types'

type AnyResult = SequenceAnalysisResult | MoleculeAnalysisResult | Record<string, unknown>

export function useAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnyResult | null>(null)
  const [status, setStatus] = useState<JobStatus>('idle')

  const analyze = useCallback(async (type: 'sequence' | 'molecule', data: Record<string, unknown>) => {
    setLoading(true)
    setError(null)
    setStatus('loading')
    try {
      let res: AnyResult
      if (type === 'sequence') {
        res = await analyzeSequence(data.sequence as string, data.sequenceType as string)
      } else {
        res = await analyzeMolecule(data.smiles as string)
      }
      setResult(res)
      setStatus('success')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed'
      setError(msg)
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setStatus('idle')
  }, [])

  return { loading, error, result, status, analyze, reset }
}
