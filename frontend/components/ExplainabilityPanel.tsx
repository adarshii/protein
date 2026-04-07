'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Info } from 'lucide-react'
import type { SHAPExplanation } from '@/lib/types'

interface ExplainabilityPanelProps {
  explanation: SHAPExplanation
  predictionScore?: number
  modelName?: string
}

export default function ExplainabilityPanel({
  explanation,
  predictionScore,
  modelName,
}: ExplainabilityPanelProps) {
  const { feature_names, shap_values, base_value } = explanation

  const data = feature_names
    .map((name, i) => ({ name, value: shap_values[i] }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 15)

  const maxAbs = Math.max(...data.map((d) => Math.abs(d.value)))

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-2">
        <Info className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-slate-800 text-sm">
            Model Explainability {modelName ? `— ${modelName}` : ''}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            SHAP values show the contribution of each feature to the prediction. Positive values
            (blue) push toward the positive class; negative values (red) push away.
          </p>
        </div>
      </div>

      {/* Base value + prediction */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-50 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-400">Base Value (expected)</p>
          <p className="text-lg font-bold text-slate-700">{base_value.toFixed(3)}</p>
        </div>
        {predictionScore !== undefined && (
          <div className="bg-primary-50 rounded-lg p-3 text-center">
            <p className="text-xs text-primary-400">Prediction Score</p>
            <p className="text-lg font-bold text-primary-700">{predictionScore.toFixed(3)}</p>
          </div>
        )}
      </div>

      {/* SHAP bar chart */}
      <div>
        <h4 className="text-sm font-semibold text-slate-700 mb-2">Feature Importance (SHAP)</h4>
        <ResponsiveContainer width="100%" height={Math.max(200, data.length * 24)}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 40, left: 80, bottom: 4 }}
          >
            <XAxis
              type="number"
              domain={[-maxAbs * 1.1, maxAbs * 1.1]}
              tick={{ fontSize: 10 }}
              tickFormatter={(v) => v.toFixed(2)}
            />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={75} />
            <Tooltip
              formatter={(value: number) => [value.toFixed(4), 'SHAP value']}
              cursor={{ fill: 'rgba(0,0,0,0.04)' }}
            />
            <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={1} />
            <Bar dataKey="value" radius={[0, 3, 3, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.value >= 0 ? '#3b82f6' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-blue-500 inline-block" />
          Positive contribution (increases prediction)
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-red-500 inline-block" />
          Negative contribution (decreases prediction)
        </div>
      </div>
    </div>
  )
}
