import AnalysisPanel from '@/components/AnalysisPanel'

export const metadata = { title: 'Analysis' }

export default function AnalysisPage() {
  return (
    <div className="animate-fade-in">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-800">Sequence &amp; Molecule Analysis</h2>
        <p className="text-slate-500 mt-1">
          Analyze DNA, RNA, and protein sequences, or compute molecular descriptors for small
          molecules.
        </p>
      </div>
      <AnalysisPanel />
    </div>
  )
}
