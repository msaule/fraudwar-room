'use client'

import { useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  BriefcaseBusiness,
  FileText,
  GitBranch,
  Network,
  Radar,
  Scale,
  ShieldCheck
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import dynamic from 'next/dynamic'
import { compact, money, pct } from '@/lib/format'

const EvidenceGraph = dynamic(
  () => import('@/visualizations/evidence-graph').then((mod) => mod.EvidenceGraph),
  { ssr: false }
)

type Run = {
  run_id: string
  days?: number
  experiment_name: string
  defense_name: string
  metrics: {
    classification: Record<string, number>
    financial: Record<string, number>
    operations: Record<string, number>
    graph: Record<string, number>
    adversarial: Record<string, number>
  }
  entities?: Record<string, number>
  rings: Array<{
    ring_id: string
    ring_type: string
    active: boolean
    detected: boolean
    disrupted: boolean
    members: string[]
    merchants: string[]
  }>
  cases: Array<{
    case_id: string
    ring_id: string | null
    priority_score: number
    dollar_exposure: number
    recommended_action: string
    status: string
  }>
  timeline: Array<{ day: number; type: string; title: string; detail: string }>
  graph: {
    nodes: Array<{ id: string; label: string; type: string; ring_id?: string | null }>
    edges: Array<{ source: string; target: string; type: string }>
  }
  defense_comparison: Array<{
    defense: string
    precision: number
    recall: number
    alerts: number
    ring_level_recall: number
  }>
  report: any
}

type View =
  | 'command'
  | 'battlefield'
  | 'rings'
  | 'cases'
  | 'experiments'
  | 'defense-lab'
  | 'after-action'
  | 'methodology'

export function Dashboard({ run, view = 'command' }: { run: Run; view?: View }) {
  const metrics = run.metrics
  const [dayLimit, setDayLimit] = useState(run.days ?? 30)
  const [ringFilter, setRingFilter] = useState('all')
  const [threshold, setThreshold] = useState(46)
  const [alertBudget, setAlertBudget] = useState(72)
  const timeline = run.timeline.filter((event) => event.day <= dayLimit).slice(0, 24)
  const activeRings = run.rings.filter((ring) => ring.active).length
  const caseRows = run.cases.slice(0, view === 'cases' ? 40 : 9)
  const decay = buildDecaySeries(metrics.adversarial)
  const filteredGraph = useMemo(
    () => filterGraph(run.graph, ringFilter),
    [run.graph, ringFilter]
  )
  const title = viewTitle(view, run.experiment_name)
  const projectedAlerts = Math.max(
    0,
    Math.round((run.defense_comparison.find((row) => row.defense.includes('graph'))?.alerts ?? 0) * (100 - threshold) / 54)
  )

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>FraudWar Room</strong>
          <span>Adaptive fraud simulation and investigation cockpit</span>
        </div>
        <nav className="nav">
          <a className={view === 'command' ? 'active' : ''} href="/"><Radar size={16} /> Command Center</a>
          <a className={view === 'battlefield' ? 'active' : ''} href="/battlefield"><Network size={16} /> Battlefield</a>
          <a className={view === 'rings' ? 'active' : ''} href="/rings"><GitBranch size={16} /> Rings</a>
          <a className={view === 'cases' ? 'active' : ''} href="/cases"><BriefcaseBusiness size={16} /> Cases</a>
          <a className={view === 'experiments' ? 'active' : ''} href="/experiments"><BarChart3 size={16} /> Experiments</a>
          <a className={view === 'defense-lab' ? 'active' : ''} href="/defense-lab"><BarChart3 size={16} /> Defense Lab</a>
          <a className={view === 'after-action' ? 'active' : ''} href="/after-action"><FileText size={16} /> After-Action</a>
          <a className={view === 'methodology' ? 'active' : ''} href="/methodology"><ShieldCheck size={16} /> Methodology</a>
        </nav>
      </aside>
      <main className="main" id="command">
        <header className="topbar">
          <div>
            <h1>{title}</h1>
            <p>{run.run_id} | {run.defense_name}</p>
          </div>
          <div className="status">Synthetic defensive simulator</div>
        </header>
        <section className="workspace">
          <div className="summary-grid">
            <Metric label="Prevented loss" value={money(metrics.financial.fraud_dollars_blocked)} detail="blocked synthetic exposure" />
            <Metric label="Net fraud loss" value={money(metrics.financial.fraud_dollars_missed)} detail="missed synthetic exposure" danger />
            <Metric label="Ring recall" value={pct(metrics.graph.ring_level_recall)} detail="ring-level investigation hit rate" />
            <Metric label="Half-life" value={`${metrics.adversarial.adversarial_half_life}`} detail="simulation days to 50% decay" />
            <Metric label="Investigator ROI" value={`${money(metrics.financial.investigator_roi)}/hr`} detail="net saved per review hour" />
            <Metric label="Backlog" value={compact(metrics.operations.backlog)} detail={`${activeRings} active synthetic rings`} />
          </div>

          {view === 'battlefield' && (
            <>
            <div className="toolbar">
              <label>
                Day
                <input
                  type="range"
                  min="1"
                  max={run.days ?? 30}
                  value={dayLimit}
                  onChange={(event) => setDayLimit(Number(event.target.value))}
                />
                <b>D{dayLimit}</b>
              </label>
              <label>
                Ring
                <select value={ringFilter} onChange={(event) => setRingFilter(event.target.value)}>
                  <option value="all">All rings</option>
                  {run.rings.map((ring) => (
                    <option key={ring.ring_id} value={ring.ring_id}>{ring.ring_id}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="ring-overlay">
              {ringOverlayRows(run, ringFilter).map((ring) => (
                <div className="ring-overlay-row" key={ring.ring_id}>
                  <strong>{ring.ring_id}</strong>
                  <span>{ring.ring_type}</span>
                  <b>{ring.members.length} accounts</b>
                  <b>{ring.merchants.length} merchants</b>
                  <em>{ring.detected ? 'detected' : 'monitoring'}</em>
                </div>
              ))}
            </div>
            </>
          )}

          {(view === 'command' || view === 'battlefield') && (
          <div className="grid">
            <section className="panel" id="graph">
              <div className="panel-header">
                <h2>Network Evidence</h2>
                <span>{filteredGraph.nodes.length} entities | {filteredGraph.edges.length} links</span>
              </div>
              <div className="graph-wrap">
                <EvidenceGraph graph={filteredGraph} />
              </div>
            </section>

            <div className="stack">
              <section className="panel">
                <div className="panel-header">
                  <h2>Adversarial Decay</h2>
                  <span>pre/post adaptation</span>
                </div>
                <div className="chart">
                  <ResponsiveContainer>
                    <LineChart data={decay}>
                      <CartesianGrid stroke="#252c35" />
                      <XAxis dataKey="day" stroke="#8d96a3" />
                      <YAxis stroke="#8d96a3" domain={[0, 1]} />
                      <Tooltip contentStyle={{ background: '#15181d', border: '1px solid #2a313b' }} />
                      <Line type="monotone" dataKey="recall" stroke="#c59a46" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="panel">
                <div className="panel-header">
                  <h2>Battlefield Timeline</h2>
                  <span>{timeline.length} events through D{dayLimit}</span>
                </div>
                <div className="timeline">
                  {timeline.map((event, index) => (
                    <div className="event" key={`${event.title}-${index}`}>
                      <time>D{event.day}</time>
                      <div>
                        <strong>{event.title}</strong>
                        <span>{event.detail}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
          )}

          {(view === 'command' || view === 'cases' || view === 'defense-lab' || view === 'experiments') && (
          <div className="grid">
            {(view === 'command' || view === 'cases') && (
            <section className="panel" id="cases">
              <div className="panel-header">
                <h2>Case Queue</h2>
                <span>{run.cases.length} cases sampled</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Case</th>
                      <th>Ring</th>
                      <th>Priority</th>
                      <th>Exposure</th>
                      <th>Action</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {caseRows.map((caseRow) => (
                      <tr key={caseRow.case_id}>
                        <td>{caseRow.case_id}</td>
                        <td>{caseRow.ring_id ?? 'none'}</td>
                        <td>{pct(caseRow.priority_score)}</td>
                        <td>{money(caseRow.dollar_exposure)}</td>
                        <td>{caseRow.recommended_action}</td>
                        <td>{caseRow.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            )}

            {(view === 'command' || view === 'defense-lab' || view === 'experiments') && (
            <section className="panel" id="defenses">
              <div className="panel-header">
                <h2>Defense Comparison</h2>
                <span>classification and ring outcomes</span>
              </div>
              <div className="chart">
                <ResponsiveContainer>
                  <BarChart data={run.defense_comparison}>
                    <CartesianGrid stroke="#252c35" />
                    <XAxis dataKey="defense" stroke="#8d96a3" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#8d96a3" domain={[0, 1]} />
                    <Tooltip contentStyle={{ background: '#15181d', border: '1px solid #2a313b' }} />
                    <Bar dataKey="recall" fill="#70a7a4" />
                    <Bar dataKey="ring_level_recall" fill="#c59a46" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
            )}
          </div>
          )}

          {view === 'defense-lab' && (
            <section className="panel">
              <div className="panel-header">
                <h2>Threshold Controls</h2>
                <span>projected queue pressure</span>
              </div>
              <div className="controls-grid">
                <label>
                  Score threshold
                  <input
                    type="range"
                    min="20"
                    max="92"
                    value={threshold}
                    onChange={(event) => setThreshold(Number(event.target.value))}
                  />
                  <b>{threshold}%</b>
                </label>
                <label>
                  Daily alert budget
                  <input
                    type="range"
                    min="10"
                    max="160"
                    value={alertBudget}
                    onChange={(event) => setAlertBudget(Number(event.target.value))}
                  />
                  <b>{alertBudget}</b>
                </label>
                <div className="control-result">
                  <strong>{projectedAlerts}</strong>
                  <span>projected alerts before budget cap</span>
                </div>
                <div className="control-result">
                  <strong>{Math.max(0, projectedAlerts - alertBudget)}</strong>
                  <span>projected backlog pressure</span>
                </div>
              </div>
            </section>
          )}

          {(view === 'command' || view === 'rings' || view === 'after-action') && (
          <div className="grid">
            {(view === 'command' || view === 'rings') && (
            <section className="panel" id="rings">
              <div className="panel-header">
                <h2>Active Rings</h2>
                <span>abstract synthetic behavior only</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Ring</th>
                      <th>Type</th>
                      <th>Members</th>
                      <th>Merchants</th>
                      <th>Detected</th>
                      <th>Disrupted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.rings.slice(0, 10).map((ring) => (
                      <tr key={ring.ring_id}>
                        <td>{ring.ring_id}</td>
                        <td>{ring.ring_type}</td>
                        <td>{ring.members.length}</td>
                        <td>{ring.merchants.length}</td>
                        <td className={ring.detected ? 'good' : ''}>{ring.detected ? 'yes' : 'no'}</td>
                        <td className={ring.disrupted ? 'good' : ''}>{ring.disrupted ? 'yes' : 'no'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            )}

            {(view === 'command' || view === 'after-action') && (
            <section className="panel" id="report">
              <div className="panel-header">
                <h2>After-Action Summary</h2>
                <span>executive report</span>
              </div>
              <div className="report">
                <ReportRow icon={<Scale size={16} />} title="Recommendation" text={run.report.recommendation} />
                <ReportRow icon={<AlertTriangle size={16} />} title="Top risk" text={run.report.executive_summary.top_risk} />
                <ReportRow icon={<ShieldCheck size={16} />} title="Boundary" text={run.report.disclaimer} />
              </div>
            </section>
            )}
          </div>
          )}

          {view === 'experiments' && (
            <section className="panel">
              <div className="panel-header">
                <h2>Experiment Registry</h2>
                <span>implemented benchmark scenarios</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Experiment</th>
                      <th>Question</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {experimentRows().map((row) => (
                      <tr key={row.name}>
                        <td>{row.name}</td>
                        <td>{row.question}</td>
                        <td>{row.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {view === 'methodology' && (
            <section className="panel">
              <div className="panel-header">
                <h2>Methodology</h2>
                <span>synthetic-only evaluation boundary</span>
              </div>
              <div className="method-grid">
                {Object.entries(run.entities ?? {}).map(([key, value]) => (
                  <div className="method-item" key={key}>
                    <strong>{compact(value)}</strong>
                    <span>{key.replaceAll('_', ' ')}</span>
                  </div>
                ))}
              </div>
              <p className="method-copy">
                Labels are synthetic ground truth for evaluation. Investigator labels are simulated
                from that closed world for active learning. Adaptation events adjust abstract ring
                parameters and do not describe real-world abuse methods.
              </p>
            </section>
          )}

          <p className="disclaimer" id="method">
            FraudWar Room uses synthetic data and abstract adversarial behavior for defensive
            research, analytics, and portfolio demonstration. It is not a guide to committing
            fraud and must not be used to facilitate abuse.
          </p>
        </section>
      </main>
    </div>
  )
}

function Metric({
  label,
  value,
  detail,
  danger
}: {
  label: string
  value: string
  detail: string
  danger?: boolean
}) {
  return (
    <div className="metric">
      <label>{label}</label>
      <strong className={danger ? 'risk' : ''}>{value}</strong>
      <span>{detail}</span>
    </div>
  )
}

function ReportRow({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="report-row">
      <strong>{icon} {title}</strong>
      <span>{text}</span>
    </div>
  )
}

function buildDecaySeries(adversarial: Record<string, number>) {
  const start = adversarial.pre_adaptation_recall || 0.7
  const end = adversarial.post_adaptation_recall || Math.max(0.2, start - 0.25)
  return Array.from({ length: 12 }, (_, i) => ({
    day: i + 1,
    recall: Number((start + (end - start) * (i / 11)).toFixed(3))
  }))
}

function filterGraph(graph: Run['graph'], ringFilter: string) {
  if (ringFilter === 'all') {
    return graph
  }
  const directlyIncluded = new Set(
    graph.nodes
      .filter((node) => node.id === ringFilter || node.ring_id === ringFilter)
      .map((node) => node.id)
  )
  const edges = graph.edges.filter(
    (edge) => directlyIncluded.has(edge.source) || directlyIncluded.has(edge.target)
  )
  for (const edge of edges) {
    directlyIncluded.add(edge.source)
    directlyIncluded.add(edge.target)
  }
  return {
    nodes: graph.nodes.filter((node) => directlyIncluded.has(node.id)),
    edges
  }
}

function viewTitle(view: View, fallback: string) {
  const titles: Record<View, string> = {
    command: fallback,
    battlefield: 'Battlefield',
    rings: 'Rings',
    cases: 'Cases',
    experiments: 'Experiments',
    'defense-lab': 'Defense Lab',
    'after-action': 'After-Action Report',
    methodology: 'Methodology'
  }
  return titles[view]
}

function experimentRows() {
  return [
    {
      name: 'Static Fraud vs Adaptive Fraud',
      question: 'Which defense survives abstract ring adaptation?',
      status: 'implemented'
    },
    {
      name: 'Transaction Model vs Graph Model',
      question: 'Which detects coordinated rings earlier?',
      status: 'implemented'
    },
    {
      name: 'Recall vs Investigator Overload',
      question: 'When does higher recall become operationally unusable?',
      status: 'implemented'
    },
    {
      name: 'Ring Takedown vs Account Takedown',
      question: 'Does ring-priority review improve dollars per hour?',
      status: 'implemented'
    },
    {
      name: 'Active Learning Under Drift',
      question: 'Do simulated labels improve post-adaptation scoring?',
      status: 'implemented'
    },
    {
      name: 'Adaptive Thresholding',
      question: 'Can thresholds respect queue pressure?',
      status: 'implemented'
    }
  ]
}

function ringOverlayRows(run: Run, ringFilter: string) {
  const rows = ringFilter === 'all'
    ? run.rings.slice(0, 6)
    : run.rings.filter((ring) => ring.ring_id === ringFilter)
  return rows.length ? rows : run.rings.slice(0, 1)
}
