import EvidencePanel from '@/components/EvidencePanel'

export const metadata = { title: 'Evidence' }

export default function EvidencePage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-800">Clinical Evidence</h2>
        <p className="text-slate-500 mt-1">
          Drug-target interaction prediction, ADMET profiling, and clinical evidence mining.
        </p>
      </div>
      <EvidencePanel />
    </div>
  )
}
