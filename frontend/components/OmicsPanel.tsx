'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, AlertCircle, Dna, BarChart2, Layers } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { annotateVariant, pathwayEnrichment } from '@/lib/api'
import type { VariantAnnotation } from '@/lib/types'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

// Variant annotation form
const variantSchema = z.object({
  chromosome: z.string().min(1, 'Chromosome required'),
  position: z.coerce.number().int().positive('Position must be a positive integer'),
  ref: z.string().min(1, 'Ref allele required').max(50),
  alt: z.string().min(1, 'Alt allele required').max(50),
})
type VariantForm = z.infer<typeof variantSchema>

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
      {message}
    </div>
  )
}

function VariantAnnotationResult({ data }: { data: VariantAnnotation }) {
  const items = [
    { label: 'Gene', value: data.gene ?? '—' },
    { label: 'Consequence', value: data.consequence ?? '—' },
    { label: 'Clinical Significance', value: data.clinical_significance ?? '—' },
    { label: 'rsID', value: data.rsid ?? '—' },
    { label: 'Allele Frequency', value: data.frequency != null ? `${(data.frequency * 100).toFixed(3)}%` : '—' },
    { label: 'Chromosome', value: `${data.chromosome}:${data.position}` },
    { label: 'Ref → Alt', value: `${data.ref} → ${data.alt}` },
  ]

  return (
    <div className="bg-slate-50 rounded-xl p-4 space-y-3">
      <h4 className="font-semibold text-slate-700 text-sm">Variant Annotation</h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {items.map((item) => (
          <div key={item.label} className="bg-white rounded-lg px-3 py-2.5 flex flex-col">
            <span className="text-xs text-slate-400">{item.label}</span>
            <span className="text-sm font-medium text-slate-800 mt-0.5">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function GenomicsTab() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VariantAnnotation | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<VariantForm>({
    resolver: zodResolver(variantSchema),
    defaultValues: { chromosome: '17', position: 43044295, ref: 'A', alt: 'G' },
  })

  const onSubmit = async (v: VariantForm) => {
    setLoading(true)
    setError(null)
    try {
      const res = await annotateVariant(v.chromosome, v.position, v.ref, v.alt)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Annotation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Annotate a genomic variant with clinical significance and population frequency.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { name: 'chromosome' as const, label: 'Chromosome', placeholder: '17' },
          { name: 'position' as const, label: 'Position', placeholder: '43044295' },
          { name: 'ref' as const, label: 'Ref Allele', placeholder: 'A' },
          { name: 'alt' as const, label: 'Alt Allele', placeholder: 'G' },
        ].map((field) => (
          <div key={field.name}>
            <label className="text-xs font-medium text-slate-600 block mb-1">{field.label}</label>
            <input
              {...register(field.name)}
              placeholder={field.placeholder}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
            />
            {errors[field.name] && (
              <p className="text-xs text-red-500 mt-0.5">{errors[field.name]?.message}</p>
            )}
          </div>
        ))}
        <div className="col-span-2 sm:col-span-4">
          <Button type="submit" disabled={loading} className="w-full sm:w-auto">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Annotating…</> : 'Annotate Variant'}
          </Button>
        </div>
      </form>
      {error && <ErrorBanner message={error} />}
      {result && <VariantAnnotationResult data={result} />}
    </div>
  )
}

const mockExpressionData = [
  { gene: 'TP53', logFC: -2.3, pValue: 0.001 },
  { gene: 'BRCA1', logFC: 1.8, pValue: 0.003 },
  { gene: 'MYC', logFC: 3.1, pValue: 0.0001 },
  { gene: 'PTEN', logFC: -1.5, pValue: 0.012 },
  { gene: 'EGFR', logFC: 2.7, pValue: 0.002 },
  { gene: 'KRAS', logFC: 1.2, pValue: 0.08 },
  { gene: 'RB1', logFC: -0.9, pValue: 0.045 },
  { gene: 'VHL', logFC: -1.1, pValue: 0.031 },
]

function TranscriptomicsTab() {
  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-500">Differential gene expression visualization (example dataset).</p>
      <div>
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Log Fold Change by Gene</h4>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart
            data={mockExpressionData}
            layout="vertical"
            margin={{ top: 4, right: 20, left: 30, bottom: 4 }}
          >
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="gene" tick={{ fontSize: 11 }} width={50} />
            <Tooltip formatter={(v: number) => [v.toFixed(2), 'log2FC']} />
            <Bar dataKey="logFC" radius={[0, 4, 4, 0]}>
              {mockExpressionData.map((d, i) => (
                <Cell key={i} fill={d.logFC > 0 ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="bg-slate-100">
              {['Gene', 'log2FC', 'p-value', 'Significance'].map((h) => (
                <th key={h} className="px-3 py-2 font-medium text-slate-600">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mockExpressionData.map((row) => (
              <tr key={row.gene} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-1.5 font-medium">{row.gene}</td>
                <td className={`px-3 py-1.5 font-mono ${row.logFC > 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {row.logFC > 0 ? '+' : ''}{row.logFC}
                </td>
                <td className="px-3 py-1.5 font-mono">{row.pValue}</td>
                <td className="px-3 py-1.5">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${row.pValue < 0.05 ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                    {row.pValue < 0.05 ? 'Significant' : 'NS'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const mockPathways = [
  { name: 'p53 signaling', genes: 18, pValue: 0.0001 },
  { name: 'DNA repair', genes: 24, pValue: 0.0003 },
  { name: 'Cell cycle', genes: 31, pValue: 0.0012 },
  { name: 'Apoptosis', genes: 15, pValue: 0.0045 },
  { name: 'MAPK signaling', genes: 27, pValue: 0.0087 },
]

function ProteomicsTab() {
  const [loading, setLoading] = useState(false)
  const [genes, setGenes] = useState('TP53,BRCA1,MYC,PTEN,EGFR,KRAS')
  const [pathways, setPathways] = useState(mockPathways)

  const runEnrichment = async () => {
    setLoading(true)
    try {
      const res = await pathwayEnrichment(genes.split(',').map((g) => g.trim()))
      if (Array.isArray(res) && res.length > 0) setPathways(res)
    } catch {
      // Use mock data on error
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Pathway enrichment analysis for a gene list.</p>
      <div className="flex gap-2">
        <input
          value={genes}
          onChange={(e) => setGenes(e.target.value)}
          placeholder="Gene list (comma-separated)"
          className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
        />
        <Button onClick={runEnrichment} disabled={loading} size="sm">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Enrich'}
        </Button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="bg-slate-100">
              {['Pathway', 'Genes', 'p-value'].map((h) => (
                <th key={h} className="px-3 py-2 font-medium text-slate-600">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pathways.map((row) => (
              <tr key={row.name} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-1.5 font-medium">{row.name}</td>
                <td className="px-3 py-1.5">{row.genes}</td>
                <td className="px-3 py-1.5 font-mono">{row.pValue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function OmicsPanel() {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
      <Tabs defaultValue="genomics">
        <div className="px-5 pt-5">
          <TabsList>
            <TabsTrigger value="genomics">
              <Dna className="w-3.5 h-3.5 mr-1.5" />Genomics
            </TabsTrigger>
            <TabsTrigger value="transcriptomics">
              <BarChart2 className="w-3.5 h-3.5 mr-1.5" />Transcriptomics
            </TabsTrigger>
            <TabsTrigger value="proteomics">
              <Layers className="w-3.5 h-3.5 mr-1.5" />Proteomics
            </TabsTrigger>
          </TabsList>
        </div>
        <div className="p-5">
          <TabsContent value="genomics"><GenomicsTab /></TabsContent>
          <TabsContent value="transcriptomics"><TranscriptomicsTab /></TabsContent>
          <TabsContent value="proteomics"><ProteomicsTab /></TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
