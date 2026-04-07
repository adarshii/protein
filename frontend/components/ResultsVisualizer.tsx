'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { formatNumber } from '@/lib/utils'
import type { SequenceAnalysisResult, MoleculeAnalysisResult } from '@/lib/types'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

interface ResultsVisualizerProps {
  result: SequenceAnalysisResult | MoleculeAnalysisResult | Record<string, unknown>
  type: 'sequence' | 'molecule'
}

function StatBadge({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 rounded-lg px-4 py-3 text-center">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-base font-bold text-slate-800">{value}</p>
    </div>
  )
}

export function ResultsVisualizer({ result, type }: ResultsVisualizerProps) {
  if (!result) return null

  if (type === 'sequence') {
    const r = result as SequenceAnalysisResult
    const compositionData = Object.entries(r.composition ?? {}).map(([name, value]) => ({
      name,
      value: Number((value * 100).toFixed(2)),
    }))

    return (
      <div className="space-y-5">
        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatBadge label="Length" value={r.length?.toLocaleString() ?? '—'} />
          <StatBadge label="Type" value={r.sequence_type ?? '—'} />
          {r.gc_content !== undefined && (
            <StatBadge label="GC Content" value={`${(r.gc_content * 100).toFixed(1)}%`} />
          )}
          {r.molecular_weight !== undefined && (
            <StatBadge label="Mol. Weight" value={`${formatNumber(r.molecular_weight)} Da`} />
          )}
        </div>

        {/* Composition bar chart */}
        {compositionData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-700 mb-3">Nucleotide / AA Composition (%)</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={compositionData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v}%`, 'Frequency']} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {compositionData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ORFs */}
        {r.orfs && r.orfs.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-700 mb-2">
              Open Reading Frames ({r.orfs.length})
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="bg-slate-100">
                    {['Start', 'End', 'Strand', 'Frame', 'Length (bp)'].map((h) => (
                      <th key={h} className="px-3 py-2 font-medium text-slate-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {r.orfs.slice(0, 10).map((orf, i) => (
                    <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-1.5">{orf.start}</td>
                      <td className="px-3 py-1.5">{orf.end}</td>
                      <td className="px-3 py-1.5">{orf.strand}</td>
                      <td className="px-3 py-1.5">{orf.frame}</td>
                      <td className="px-3 py-1.5">{orf.length}</td>
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

  // Molecule result
  const r = result as MoleculeAnalysisResult
  const descriptorData = [
    { name: 'MW', value: r.molecular_weight },
    { name: 'LogP', value: r.logp },
    { name: 'HBD', value: r.hbd },
    { name: 'HBA', value: r.hba },
    { name: 'TPSA', value: r.tpsa },
    { name: 'RotBonds', value: r.rotatable_bonds },
  ].filter((d) => d.value !== undefined)

  const lipinskiItems = [
    { label: 'MW ≤ 500', pass: r.molecular_weight <= 500 },
    { label: 'LogP ≤ 5', pass: r.logp <= 5 },
    { label: 'HBD ≤ 5', pass: r.hbd <= 5 },
    { label: 'HBA ≤ 10', pass: r.hba <= 10 },
  ]

  const compositionPieData = descriptorData.map((d) => ({
    name: d.name,
    value: Math.abs(d.value),
  }))

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatBadge label="Mol. Weight" value={`${formatNumber(r.molecular_weight)} Da`} />
        <StatBadge label="LogP" value={formatNumber(r.logp)} />
        <StatBadge label="TPSA" value={`${formatNumber(r.tpsa)} Å²`} />
        <StatBadge label="HBD" value={r.hbd} />
        <StatBadge label="HBA" value={r.hba} />
        <StatBadge label="Rotatable Bonds" value={r.rotatable_bonds} />
      </div>

      {/* Lipinski */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h4 className="text-sm font-semibold text-slate-700">Lipinski Rule of Five</h4>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${r.lipinski_passes ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {r.lipinski_passes ? '✓ Passes' : '✗ Fails'}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {lipinskiItems.map((item) => (
            <span
              key={item.label}
              className={`px-2.5 py-1 rounded-md text-xs font-medium ${item.pass ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}
            >
              {item.pass ? '✓' : '✗'} {item.label}
            </span>
          ))}
        </div>
      </div>

      {/* Bar chart */}
      <div>
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Molecular Descriptors</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={descriptorData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {descriptorData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={compositionPieData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                dataKey="value"
                label={({ name }) => name}
                labelLine={false}
              >
                {compositionPieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Legend iconSize={10} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
