'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Search, AlertCircle } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { SequenceInput } from '@/components/SequenceInput'
import { ResultsVisualizer } from '@/components/ResultsVisualizer'
import { useAnalysis } from '@/hooks/useAnalysis'
import { findORFs, pairwiseAlignment } from '@/lib/api'
import { MOLECULE_EXAMPLE_SMILES } from '@/lib/constants'

// Molecule form schema
const moleculeSchema = z.object({
  smiles: z.string().min(2, 'Enter a valid SMILES string'),
})
type MolForm = z.infer<typeof moleculeSchema>

// Alignment form schema
const alignSchema = z.object({
  seq1: z.string().min(4, 'Sequence 1 required'),
  seq2: z.string().min(4, 'Sequence 2 required'),
  algorithm: z.string(),
})
type AlignForm = z.infer<typeof alignSchema>

function MoleculeAnalysisTab() {
  const { loading, error, result, analyze } = useAnalysis()
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<MolForm>({
    resolver: zodResolver(moleculeSchema),
  })

  return (
    <div className="space-y-4">
      <form
        onSubmit={handleSubmit((v) => analyze('molecule', { smiles: v.smiles }))}
        className="space-y-3"
      >
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1">SMILES String</label>
          <input
            {...register('smiles')}
            placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300"
          />
          {errors.smiles && <p className="text-xs text-red-500 mt-1">{errors.smiles.message}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          {MOLECULE_EXAMPLE_SMILES.map((m) => (
            <button
              key={m.label}
              type="button"
              onClick={() => setValue('smiles', m.smiles)}
              className="px-2.5 py-1 text-xs rounded-md bg-slate-100 hover:bg-primary-50 hover:text-primary-700 text-slate-600 transition-colors"
            >
              {m.label}
            </button>
          ))}
        </div>
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</> : 'Analyze Molecule'}
        </Button>
      </form>
      {error && <ErrorBanner message={error} />}
      {result && <ResultsVisualizer result={result} type="molecule" />}
    </div>
  )
}

function AlignmentTab() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const { register, handleSubmit, formState: { errors } } = useForm<AlignForm>({
    resolver: zodResolver(alignSchema),
    defaultValues: { algorithm: 'needleman_wunsch' },
  })

  const onSubmit = async (v: AlignForm) => {
    setLoading(true)
    setError(null)
    try {
      const res = await pairwiseAlignment(v.seq1, v.seq2, v.algorithm)
      setResult(res as unknown as Record<string, unknown>)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Alignment failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1">Sequence 1</label>
          <textarea
            {...register('seq1')}
            rows={3}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
            placeholder="ATGGCCATTGTAATG…"
          />
          {errors.seq1 && <p className="text-xs text-red-500 mt-1">{errors.seq1.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1">Sequence 2</label>
          <textarea
            {...register('seq2')}
            rows={3}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
            placeholder="ATGGCGGTTGTAATG…"
          />
          {errors.seq2 && <p className="text-xs text-red-500 mt-1">{errors.seq2.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1">Algorithm</label>
          <select
            {...register('algorithm')}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
          >
            <option value="needleman_wunsch">Needleman-Wunsch (Global)</option>
            <option value="smith_waterman">Smith-Waterman (Local)</option>
          </select>
        </div>
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Aligning…</> : <><Search className="w-4 h-4" /> Run Alignment</>}
        </Button>
      </form>
      {error && <ErrorBanner message={error} />}
      {result && (
        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3 text-center">
            {['score', 'identity', 'gaps'].map((k) => (
              <div key={k} className="bg-white rounded-lg p-3 shadow-sm">
                <p className="text-xs text-slate-500 capitalize">{k}</p>
                <p className="text-lg font-bold text-slate-800">
                  {typeof result[k] === 'number'
                    ? k === 'identity'
                      ? `${((result[k] as number) * 100).toFixed(1)}%`
                      : (result[k] as number).toFixed(1)
                    : '—'}
                </p>
              </div>
            ))}
          </div>
          {typeof result.aligned_seq1 === 'string' && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Aligned sequences</p>
              <pre className="text-xs font-mono bg-white rounded border border-slate-200 p-3 overflow-x-auto whitespace-pre-wrap break-all">
                {result.aligned_seq1}
                {'\n'}
                {typeof result.aligned_seq2 === 'string' ? result.aligned_seq2 : ''}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ORFTab() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ orfs: unknown[]; total: number } | null>(null)
  const [seq, setSeq] = useState('')
  const [minLen, setMinLen] = useState(100)

  const run = async () => {
    if (!seq.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await findORFs(seq, minLen)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'ORF finding failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium text-slate-700 block mb-1">DNA Sequence</label>
        <textarea
          value={seq}
          onChange={(e) => setSeq(e.target.value)}
          rows={5}
          placeholder="Paste DNA sequence…"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
        />
      </div>
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-slate-700 whitespace-nowrap">Min ORF length (bp):</label>
        <input
          type="number"
          value={minLen}
          onChange={(e) => setMinLen(Number(e.target.value))}
          className="w-24 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
          min={30}
          max={10000}
        />
      </div>
      <Button onClick={run} disabled={loading || !seq.trim()} className="w-full">
        {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Finding ORFs…</> : 'Find ORFs'}
      </Button>
      {error && <ErrorBanner message={error} />}
      {result && (
        <div>
          <p className="text-sm font-semibold text-slate-700 mb-2">
            Found {result.total} ORF{result.total !== 1 ? 's' : ''}
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-slate-100">
                  {['#', 'Start', 'End', 'Strand', 'Frame', 'Length'].map((h) => (
                    <th key={h} className="px-3 py-2 font-medium text-slate-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(result.orfs as Array<Record<string, unknown>>).slice(0, 20).map((orf, i) => (
                  <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-1.5">{i + 1}</td>
                    <td className="px-3 py-1.5">{orf.start as number}</td>
                    <td className="px-3 py-1.5">{orf.end as number}</td>
                    <td className="px-3 py-1.5">{orf.strand as string}</td>
                    <td className="px-3 py-1.5">{orf.frame as number}</td>
                    <td className="px-3 py-1.5">{orf.length as number}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
      {message}
    </div>
  )
}

export default function AnalysisPanel() {
  const { loading, error, result, analyze } = useAnalysis()

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
      <Tabs defaultValue="sequence">
        <div className="px-5 pt-5">
          <TabsList className="w-full sm:w-auto overflow-x-auto">
            <TabsTrigger value="sequence">Sequence Analysis</TabsTrigger>
            <TabsTrigger value="molecule">Molecule Analysis</TabsTrigger>
            <TabsTrigger value="alignment">Alignment</TabsTrigger>
            <TabsTrigger value="orf">ORF Finding</TabsTrigger>
          </TabsList>
        </div>

        <div className="p-5">
          <TabsContent value="sequence">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <SequenceInput
                  onSubmit={(v) => analyze('sequence', { sequence: v.sequence, sequenceType: v.sequenceType })}
                  loading={loading}
                />
                {error && <ErrorBanner message={error} />}
              </div>
              {result && (
                <div>
                  <h3 className="font-semibold text-slate-700 mb-4">Results</h3>
                  <ResultsVisualizer result={result} type="sequence" />
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="molecule">
            <MoleculeAnalysisTab />
          </TabsContent>

          <TabsContent value="alignment">
            <AlignmentTab />
          </TabsContent>

          <TabsContent value="orf">
            <ORFTab />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
