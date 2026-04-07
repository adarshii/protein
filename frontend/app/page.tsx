import Link from 'next/link'
import { ArrowRight, Dna, FlaskConical, Brain, BarChart3 } from 'lucide-react'

const features = [
  {
    icon: Dna,
    title: 'Sequence Analysis',
    description:
      'Analyze DNA, RNA, and protein sequences. Compute composition, find ORFs, perform alignments, and predict structures.',
    color: 'text-blue-500',
    bg: 'bg-blue-50',
  },
  {
    icon: FlaskConical,
    title: 'Molecular Descriptors',
    description:
      'Compute physicochemical properties, fingerprints, and ADMET predictions for small molecules using RDKit.',
    color: 'text-green-500',
    bg: 'bg-green-50',
  },
  {
    icon: Brain,
    title: 'ML-Powered Predictions',
    description:
      'Drug-target interaction prediction, toxicity screening, and bioactivity modeling with explainable AI (SHAP).',
    color: 'text-purple-500',
    bg: 'bg-purple-50',
  },
  {
    icon: BarChart3,
    title: 'Omics Integration',
    description:
      'Variant annotation, gene expression analysis, pathway enrichment, and multi-omics data visualization.',
    color: 'text-orange-500',
    bg: 'bg-orange-50',
  },
]

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Nav */}
      <nav className="border-b border-white/60 bg-white/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Dna className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-slate-800 text-lg">BioChemAI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-50 border border-primary-100 text-primary-700 text-xs font-medium mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
          AI-Powered Bioinformatics &amp; Chemoinformatics
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
          BioChemAI{' '}
          <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
            Platform
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-xl text-slate-600 leading-relaxed mb-10">
          A unified platform for sequence analysis, molecular property prediction, omics data
          integration, and clinical evidence mining — accelerating drug discovery and genomics
          research.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-primary-600 text-white font-semibold text-base hover:bg-primary-700 transition-all shadow-lg shadow-primary-200 hover:shadow-primary-300 hover:-translate-y-0.5"
          >
            Go to Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/dashboard/analysis"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-white text-slate-700 font-semibold text-base hover:bg-slate-50 transition-all border border-slate-200 shadow-sm hover:-translate-y-0.5"
          >
            Start Analyzing
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 mb-3">Everything you need</h2>
          <p className="text-slate-500 text-lg">
            From raw sequences to clinical insights in one platform.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="group bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md transition-all hover:-translate-y-1"
            >
              <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                <f.icon className={`w-6 h-6 ${f.color}`} />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">{f.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-400">
        © {new Date().getFullYear()} BioChemAI Platform. Built with Next.js 14 &amp; FastAPI.
      </footer>
    </main>
  )
}
