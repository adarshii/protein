import ModelPanel from '@/components/ModelPanel'

export const metadata = { title: 'Models' }

export default function ModelsPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-800">ML Models</h2>
        <p className="text-slate-500 mt-1">
          Browse available machine learning models, view performance metrics, and run predictions.
        </p>
      </div>
      <ModelPanel />
    </div>
  )
}
