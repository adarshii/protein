import Link from 'next/link'
import { FlaskConical, Dna, BookOpen, BrainCircuit, Activity } from 'lucide-react'

const stats = [
  { label: 'Analyses Run', value: '2,847', change: '+12% this week', color: 'text-blue-600', bg: 'bg-blue-50' },
  { label: 'Molecules Analyzed', value: '1,203', change: '+8% this week', color: 'text-green-600', bg: 'bg-green-50' },
  { label: 'Models Available', value: '14', change: '3 recently added', color: 'text-purple-600', bg: 'bg-purple-50' },
  { label: 'Active Jobs', value: '5', change: '2 in queue', color: 'text-orange-600', bg: 'bg-orange-50' },
]

const recentActivity = [
  { id: 1, type: 'Sequence Analysis', name: 'BRCA1 gene variant analysis', time: '2 min ago', status: 'completed' },
  { id: 2, type: 'Molecule Analysis', name: 'Aspirin descriptor computation', time: '15 min ago', status: 'completed' },
  { id: 3, type: 'DTI Prediction', name: 'Ibuprofen-COX2 interaction', time: '1 hr ago', status: 'completed' },
  { id: 4, type: 'Variant Annotation', name: 'VCF file annotation batch', time: '3 hr ago', status: 'running' },
  { id: 5, type: 'ORF Finding', name: 'Novel bacterial sequence', time: '5 hr ago', status: 'completed' },
]

const quickActions = [
  { href: '/dashboard/analysis', label: 'New Sequence Analysis', icon: FlaskConical, color: 'bg-blue-600 hover:bg-blue-700' },
  { href: '/dashboard/omics', label: 'Omics Analysis', icon: Dna, color: 'bg-green-600 hover:bg-green-700' },
  { href: '/dashboard/evidence', label: 'Evidence Search', icon: BookOpen, color: 'bg-purple-600 hover:bg-purple-700' },
  { href: '/dashboard/models', label: 'Run ML Model', icon: BrainCircuit, color: 'bg-orange-600 hover:bg-orange-700' },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Welcome back</h2>
        <p className="text-slate-500 mt-1">Here's what's happening on your platform.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl p-5 border border-slate-100 shadow-sm">
            <div className={`inline-flex w-10 h-10 rounded-lg ${stat.bg} items-center justify-center mb-3`}>
              <Activity className={`w-5 h-5 ${stat.color}`} />
            </div>
            <p className="text-2xl font-bold text-slate-800">{stat.value}</p>
            <p className="text-sm font-medium text-slate-600 mt-0.5">{stat.label}</p>
            <p className="text-xs text-slate-400 mt-1">{stat.change}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">Recent Activity</h3>
          </div>
          <div className="divide-y divide-slate-50">
            {recentActivity.map((item) => (
              <div key={item.id} className="px-5 py-3.5 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-700">{item.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{item.type} · {item.time}</p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    item.status === 'completed'
                      ? 'bg-green-50 text-green-700'
                      : 'bg-amber-50 text-amber-700'
                  }`}
                >
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">Quick Actions</h3>
          </div>
          <div className="p-4 space-y-2.5">
            {quickActions.map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-white text-sm font-medium ${action.color} transition-colors`}
              >
                <action.icon className="w-4 h-4" />
                {action.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
