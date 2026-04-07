import OmicsPanel from '@/components/OmicsPanel'

export const metadata = { title: 'Omics' }

export default function OmicsPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-800">Omics Analysis</h2>
        <p className="text-slate-500 mt-1">
          Genomics, transcriptomics, and proteomics data analysis — variant annotation, expression
          profiling, and pathway enrichment.
        </p>
      </div>
      <OmicsPanel />
    </div>
  )
}
