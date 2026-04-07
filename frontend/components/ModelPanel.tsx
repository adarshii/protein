'use client'

import { useState } from 'react'
import { Loader2, BrainCircuit, CheckCircle, TrendingUp, Play } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { formatNumber } from '@/lib/utils'

interface ModelInfo {
  id: string
  name: string
  type: string
  description: string
  accuracy: number
  auc: number
  f1: number
  version: string
  tags: string[]
}

const models: ModelInfo[] = [
  {
    id: 'dti-gnn',
    name: 'DTI-GNN',
    type: 'Graph Neural Network',
    description: 'Drug-target interaction prediction using molecular graph neural networks.',
    accuracy: 0.923,
    auc: 0.961,
    f1: 0.915,
    version: '2.1.0',
    tags: ['DTI', 'GNN', 'Drug Discovery'],
  },
  {
    id: 'toxicity-rf',
    name: 'ToxPredict-RF',
    type: 'Random Forest',
    description: 'AMES toxicity and hERG inhibition prediction from molecular fingerprints.',
    accuracy: 0.887,
    auc: 0.934,
    f1: 0.879,
    version: '1.3.2',
    tags: ['Toxicity', 'ADMET', 'Safety'],
  },
  {
    id: 'solubility-xgb',
    name: 'SolubilityXGB',
    type: 'XGBoost',
    description: 'Aqueous solubility prediction (log S) from 2D molecular descriptors.',
    accuracy: 0.856,
    auc: 0.912,
    f1: 0.848,
    version: '1.1.0',
    tags: ['Solubility', 'ADMET', 'Physicochemical'],
  },
  {
    id: 'bioactivity-lstm',
    name: 'BioActLSTM',
    type: 'LSTM',
    description: 'Bioactivity prediction against kinase targets from SMILES sequences.',
    accuracy: 0.891,
    auc: 0.947,
    f1: 0.882,
    version: '3.0.1',
    tags: ['Bioactivity', 'Kinases', 'LSTM'],
  },
  {
    id: 'prot-classifier',
    name: 'ProteinClassifier',
    type: 'Transformer',
    description: 'Protein family classification and secondary structure prediction.',
    accuracy: 0.934,
    auc: 0.978,
    f1: 0.929,
    version: '1.0.0',
    tags: ['Protein', 'Classification', 'Transformer'],
  },
]

function MetricBar({ value, color = 'bg-primary-500' }: { value: number; color?: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
      <span className="text-xs font-mono text-slate-600 w-10 text-right">{(value * 100).toFixed(1)}%</span>
    </div>
  )
}

function ModelCard({ model, onSelect }: { model: ModelInfo; onSelect: (m: ModelInfo) => void }) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-slate-800">{model.name}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{model.type} · v{model.version}</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => onSelect(model)}>
          <Play className="w-3 h-3" /> Run
        </Button>
      </div>
      <p className="text-sm text-slate-500 mb-4 leading-relaxed">{model.description}</p>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>Accuracy</span>
          <span>AUC</span>
          <span>F1</span>
        </div>
        <MetricBar value={model.accuracy} color="bg-blue-500" />
        <MetricBar value={model.auc} color="bg-green-500" />
        <MetricBar value={model.f1} color="bg-purple-500" />
      </div>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {model.tags.map((tag) => (
          <span key={tag} className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs">{tag}</span>
        ))}
      </div>
    </div>
  )
}

function PredictionInterface({ model, onClose }: { model: ModelInfo; onClose: () => void }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ value: number; label: string } | null>(null)

  const run = async () => {
    if (!input.trim()) return
    setLoading(true)
    // Simulate prediction (replace with real API call)
    await new Promise((r) => setTimeout(r, 1500))
    setResult({ value: Math.random(), label: Math.random() > 0.5 ? 'Active' : 'Inactive' })
    setLoading(false)
  }

  const placeholder =
    model.tags.includes('Protein') || model.tags.includes('DTI')
      ? 'Enter protein sequence (FASTA or plain)…'
      : 'Enter SMILES string…'

  return (
    <div className="bg-white rounded-xl border border-primary-200 shadow-md p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-primary-500" /> {model.name}
          </h3>
          <p className="text-xs text-slate-400">{model.type}</p>
        </div>
        <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-600">Close</button>
      </div>
      <div>
        <label className="text-sm font-medium text-slate-700 block mb-1">Input</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={4}
          placeholder={placeholder}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-300 resize-y"
        />
      </div>
      <Button onClick={run} disabled={loading || !input.trim()} className="w-full">
        {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Running prediction…</> : 'Run Prediction'}
      </Button>
      {result && (
        <div className="bg-slate-50 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="font-semibold text-slate-700 text-sm">Prediction Complete</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-slate-400">Prediction Score</p>
              <p className="text-2xl font-bold text-slate-800">{formatNumber(result.value)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-slate-400">Classification</p>
              <p className={`text-2xl font-bold ${result.label === 'Active' ? 'text-green-600' : 'text-red-600'}`}>
                {result.label}
              </p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>Inactive</span>
              <span>Active</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-red-400 to-green-400 transition-all"
                style={{ width: `${result.value * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ModelPerformanceTab() {
  const performanceData = models.map((m) => ({
    name: m.name,
    accuracy: m.accuracy,
    auc: m.auc,
    f1: m.f1,
  }))

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Performance comparison across all available models.</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="bg-slate-100">
              {['Model', 'Type', 'Accuracy', 'AUC-ROC', 'F1 Score', 'Version'].map((h) => (
                <th key={h} className="px-4 py-3 font-medium text-slate-600 text-xs">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {performanceData.map((row, i) => (
              <tr key={row.name} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3 font-semibold text-slate-800">{row.name}</td>
                <td className="px-4 py-3 text-slate-500 text-xs">{models[i].type}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${row.accuracy * 100}%` }} />
                    </div>
                    <span className="text-xs font-mono">{(row.accuracy * 100).toFixed(1)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${row.auc * 100}%` }} />
                    </div>
                    <span className="text-xs font-mono">{(row.auc * 100).toFixed(1)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-purple-500" style={{ width: `${row.f1 * 100}%` }} />
                    </div>
                    <span className="text-xs font-mono">{(row.f1 * 100).toFixed(1)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">v{models[i].version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function ModelPanel() {
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null)

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
      <Tabs defaultValue="models">
        <div className="px-5 pt-5">
          <TabsList>
            <TabsTrigger value="models">
              <BrainCircuit className="w-3.5 h-3.5 mr-1.5" />Available Models
            </TabsTrigger>
            <TabsTrigger value="performance">
              <TrendingUp className="w-3.5 h-3.5 mr-1.5" />Performance
            </TabsTrigger>
          </TabsList>
        </div>
        <div className="p-5">
          <TabsContent value="models">
            <div className="space-y-4">
              {selectedModel && (
                <PredictionInterface
                  model={selectedModel}
                  onClose={() => setSelectedModel(null)}
                />
              )}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {models.map((m) => (
                  <ModelCard key={m.id} model={m} onSelect={setSelectedModel} />
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="performance">
            <ModelPerformanceTab />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
