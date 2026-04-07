'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, AlertCircle, Pill, Activity, FlaskConical } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { predictDTI, predictADMET } from '@/lib/api'
import type { DTIPrediction, ADMETProperties } from '@/lib/types'
import { formatNumber } from '@/lib/utils'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from 'recharts'

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
      {message}
    </div>
  )
}

// ── DTI Prediction ────────────────────────────────────────────────────────────

const dtiSchema = z.object({
  drug_smiles: z.string().min(2, 'Enter a valid SMILES'),
  target_sequence: z.string().min(10, 'Enter a protein target sequence'),
})
type DTIForm = z.infer<typeof dtiSchema>

function DTITab() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DTIPrediction | null>(null)

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<DTIForm>({
    resolver: zodResolver(dtiSchema),
  })

  const onSubmit = async (v: DTIForm) => {
    setLoading(true)
    setError(null)
    try {
      const res = await predictDTI(v.drug_smiles, v.target_sequence)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const loadExample = () => {
    setValue('drug_smiles', 'CC(=O)Oc1ccccc1C(=O)O')
    setValue('target_sequence', 'MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY')
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Predict binding probability between a small molecule drug and a protein target.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm font-medium text-slate-700">Drug SMILES</label>
            <button type="button" onClick={loadExample} className="text-xs text-primary-600 hover:underline">
              Load example
            </button>
          </div>
          <input
            {...register('drug_smiles')}
            placeholder="CC(=O)Oc1ccccc1C(=O)O"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300"
          />
          {errors.drug_smiles && <p className="text-xs text-red-500 mt-1">{errors.drug_smiles.message}</p>}
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1">Target Protein Sequence</label>
          <textarea
            {...register('target_sequence')}
            rows={4}
            placeholder="MTEYKLVVV…"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
          />
          {errors.target_sequence && <p className="text-xs text-red-500 mt-1">{errors.target_sequence.message}</p>}
        </div>
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Predicting…</> : <><Pill className="w-4 h-4" /> Predict DTI</>}
        </Button>
      </form>
      {error && <ErrorBanner message={error} />}
      {result && (
        <div className="bg-slate-50 rounded-xl p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-slate-700">DTI Prediction Result</h4>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${result.binding_probability > 0.5 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {result.binding_probability > 0.5 ? 'Binding' : 'Non-binding'}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-slate-400">Binding Probability</p>
              <p className="text-2xl font-bold text-slate-800">{(result.binding_probability * 100).toFixed(1)}%</p>
            </div>
            {result.binding_affinity != null && (
              <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                <p className="text-xs text-slate-400">Binding Affinity (pKd)</p>
                <p className="text-2xl font-bold text-slate-800">{formatNumber(result.binding_affinity)}</p>
              </div>
            )}
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-slate-400">Confidence</p>
              <p className="text-2xl font-bold text-slate-800 capitalize">{result.confidence}</p>
            </div>
          </div>
          {/* Probability bar */}
          <div>
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span>Non-binding</span>
              <span>Binding</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all bg-gradient-to-r from-blue-400 to-green-500"
                style={{ width: `${result.binding_probability * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── ADMET ─────────────────────────────────────────────────────────────────────

function ADMETTab() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ADMETProperties | null>(null)
  const [smiles, setSmiles] = useState('')

  const run = async () => {
    if (!smiles.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await predictADMET(smiles)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'ADMET prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const radarData = result
    ? [
        { subject: 'Bioavailability', A: result.absorption.bioavailability * 100 },
        { subject: 'Absorption', A: result.absorption.intestinal_absorption * 100 },
        { subject: 'BBB', A: result.distribution.bbb_permeant ? 80 : 20 },
        { subject: 'PPB', A: result.distribution.ppb * 100 },
        { subject: 'Clearance', A: Math.min(result.excretion.clearance, 100) },
      ]
    : []

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Predict Absorption, Distribution, Metabolism, Excretion and Toxicity properties.</p>
      <div className="flex gap-2">
        <input
          value={smiles}
          onChange={(e) => setSmiles(e.target.value)}
          placeholder="Enter SMILES…"
          className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300"
        />
        <Button onClick={run} disabled={loading || !smiles.trim()}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Activity className="w-4 h-4" /> Predict</>}
        </Button>
      </div>
      {error && <ErrorBanner message={error} />}
      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2">ADMET Radar</h4>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
                  <Radar name="ADMET" dataKey="A" fill="#3b82f6" fillOpacity={0.3} stroke="#3b82f6" />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Bioavailability', value: `${(result.absorption.bioavailability * 100).toFixed(0)}%`, ok: result.absorption.bioavailability > 0.3 },
                { label: 'BBB Permeant', value: result.distribution.bbb_permeant ? 'Yes' : 'No', ok: !result.distribution.bbb_permeant },
                { label: 'Pgp Substrate', value: result.absorption.pgp_substrate ? 'Yes' : 'No', ok: !result.absorption.pgp_substrate },
                { label: 'hERG Inhibitor', value: result.toxicity.herg_inhibitor ? 'Yes' : 'No', ok: !result.toxicity.herg_inhibitor },
                { label: 'AMES Toxic', value: result.toxicity.ames_toxic ? 'Yes' : 'No', ok: !result.toxicity.ames_toxic },
                { label: 'Half-life (h)', value: `${formatNumber(result.excretion.half_life)}`, ok: true },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between bg-white rounded-lg px-3 py-2 shadow-sm">
                  <span className="text-sm text-slate-600">{item.label}</span>
                  <span className={`text-sm font-semibold ${item.ok ? 'text-green-600' : 'text-red-600'}`}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Clinical Evidence ─────────────────────────────────────────────────────────

const mockTrials = [
  { id: 'NCT03661515', name: 'BRCA1/2 Gene Therapy Phase II', phase: 'Phase II', status: 'Recruiting', drug: 'Olaparib' },
  { id: 'NCT04230902', name: 'KRAS G12C Inhibitor Study', phase: 'Phase I/II', status: 'Active', drug: 'Sotorasib' },
  { id: 'NCT05123456', name: 'PD-L1 Combination Therapy', phase: 'Phase III', status: 'Completed', drug: 'Pembrolizumab' },
  { id: 'NCT04789012', name: 'Targeted EGFR Therapy', phase: 'Phase II', status: 'Enrolling', drug: 'Erlotinib' },
]

function ClinicalTrialsTab() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Example clinical trials related to the analyzed targets (mock data).</p>
      <div className="space-y-3">
        {mockTrials.map((trial) => (
          <div key={trial.id} className="bg-slate-50 rounded-xl p-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-800">{trial.name}</p>
              <p className="text-xs text-slate-500 mt-0.5">{trial.id} · {trial.drug}</p>
              <div className="flex gap-2 mt-2">
                <span className="px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">{trial.phase}</span>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  trial.status === 'Completed' ? 'bg-green-50 text-green-700' :
                  trial.status === 'Recruiting' || trial.status === 'Enrolling' ? 'bg-amber-50 text-amber-700' :
                  'bg-slate-100 text-slate-600'
                }`}>{trial.status}</span>
              </div>
            </div>
            <a
              href={`https://clinicaltrials.gov/ct2/show/${trial.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary-600 hover:underline whitespace-nowrap"
            >
              View →
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function EvidencePanel() {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
      <Tabs defaultValue="dti">
        <div className="px-5 pt-5">
          <TabsList>
            <TabsTrigger value="dti"><Pill className="w-3.5 h-3.5 mr-1.5" />Drug-Target</TabsTrigger>
            <TabsTrigger value="admet"><FlaskConical className="w-3.5 h-3.5 mr-1.5" />ADMET</TabsTrigger>
            <TabsTrigger value="trials"><Activity className="w-3.5 h-3.5 mr-1.5" />Clinical Trials</TabsTrigger>
          </TabsList>
        </div>
        <div className="p-5">
          <TabsContent value="dti"><DTITab /></TabsContent>
          <TabsContent value="admet"><ADMETTab /></TabsContent>
          <TabsContent value="trials"><ClinicalTrialsTab /></TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
