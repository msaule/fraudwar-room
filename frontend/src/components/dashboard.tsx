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
  ShieldCheck,
  X
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
    shared_devices?: string[]
    shared_ip_clusters?: string[]
    detection_memory?: string[]
  }>
  cases: Array<{
    case_id: string
    day_opened?: number
    alert_ids?: string[]
    account_ids?: string[]
    merchant_ids?: string[]
    ring_id: string | null
    priority_score: number
    dollar_exposure: number
    false_positive_risk?: number
    recommended_action: string
    status: string
    investigator_id?: string
    review_hours?: number
    notes?: string
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

type EvidenceSelection = {
  kind: 'node' | 'case'
  id: string
}

export function Dashboard({ run, view = 'command' }: { run: Run; view?: View }) {
  const metrics = run.metrics
  const [dayLimit, setDayLimit] = useState(run.days ?? 30)
  const [ringFilter, setRingFilter] = useState('all')
  const [threshold, setThreshold] = useState(46)
  const [alertBudget, setAlertBudget] = useState(72)
  const [scenarioId, setScenarioId] = useState('static-vs-adaptive')
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceSelection | null>(null)
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  const timeline = run.timeline.filter((event) => event.day <= dayLimit).slice(0, 24)
  const activeRings = run.rings.filter((ring) => ring.active).length
  const caseRows = run.cases.slice(0, view === 'cases' ? 40 : 9)
  const decay = buildDecaySeries(metrics.adversarial)
  const scenarios = scenarioRows(run)
  const selectedScenario = scenarios.find((scenario) => scenario.id === scenarioId) ?? scenarios[0]
  const filteredGraph = useMemo(
    () => filterGraph(run.graph, ringFilter),
    [run.graph, ringFilter]
  )
  const title = viewTitle(view, run.experiment_name)
  const projectedAlerts = Math.max(
    0,
    Math.round((run.defense_comparison.find((row) => row.defense.includes('graph'))?.alerts ?? 0) * (100 - threshold) / 54)
  )
  const selectedNodeId = selectedEvidence?.kind === 'node' ? selectedEvidence.id : selectedEvidence?.id ?? null

  function selectGraphNode(id: string) {
    const node = run.graph.nodes.find((item) => item.id === id)
    setSelectedEvidence({ kind: node?.type === 'case' ? 'case' : 'node', id })
  }

  function selectCase(id: string) {
    setSelectedEvidence({ kind: 'case', id })
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>FraudWar Room</strong>
          <span>Loss, ring recall, review queue</span>
        </div>
        <nav className="nav">
          <a className={view === 'command' ? 'active' : ''} href="/"><Radar size={16} /> Overview</a>
          <a className={view === 'battlefield' ? 'active' : ''} href="/battlefield"><Network size={16} /> Evidence Map</a>
          <a className={view === 'rings' ? 'active' : ''} href="/rings"><GitBranch size={16} /> Rings</a>
          <a className={view === 'cases' ? 'active' : ''} href="/cases"><BriefcaseBusiness size={16} /> Cases</a>
          <a className={view === 'experiments' ? 'active' : ''} href="/experiments"><BarChart3 size={16} /> Experiments</a>
          <a className={view === 'defense-lab' ? 'active' : ''} href="/defense-lab"><BarChart3 size={16} /> Defense Tests</a>
          <a className={view === 'after-action' ? 'active' : ''} href="/after-action"><FileText size={16} /> Run Memo</a>
          <a className={view === 'methodology' ? 'active' : ''} href="/methodology"><ShieldCheck size={16} /> Methodology</a>
        </nav>
      </aside>
      <main className="main" id="command">
        <header className="topbar">
          <div>
            <h1>{title}</h1>
            <p>{run.run_id} | {run.defense_name}</p>
          </div>
          <div className="status">Demo data only</div>
        </header>
        <section className="workspace">
          <div className="summary-grid">
            <Metric label="Prevented loss" value={money(metrics.financial.fraud_dollars_blocked)} detail="stopped by review" />
            <Metric label="Net fraud loss" value={money(metrics.financial.fraud_dollars_missed)} detail="missed exposure" danger />
            <Metric label="Ring recall" value={pct(metrics.graph.ring_level_recall)} detail="rings with enough evidence" />
            <Metric label="Half-life" value={`${metrics.adversarial.adversarial_half_life}`} detail="days until recall halves" />
            <Metric label="Investigator ROI" value={`${money(metrics.financial.investigator_roi)}/hr`} detail="return per review hour" />
            <Metric label="Backlog" value={compact(metrics.operations.backlog)} detail={`${activeRings} active groups`} />
          </div>

          <ScenarioSelector
            scenarios={scenarios}
            selectedScenario={selectedScenario}
            value={scenarioId}
            onChange={setScenarioId}
          />

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
                <h2>Evidence Map</h2>
                <span>{filteredGraph.nodes.length} entities, {filteredGraph.edges.length} links in source graph</span>
              </div>
              <div className="graph-wrap">
                <EvidenceGraph
                  graph={filteredGraph}
                  selectedId={selectedNodeId}
                  hoverId={hoveredNodeId}
                  onSelectNode={selectGraphNode}
                  onHoverNode={setHoveredNodeId}
                />
              </div>
            </section>

            <div className="stack">
              <section className="panel">
                <div className="panel-header">
                  <h2>Recall Under Drift</h2>
                  <span>daily recall estimate</span>
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
                  <h2>Event Log</h2>
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
                <span>{run.cases.length} cases in sample queue</span>
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
                      <tr
                        className={selectedEvidence?.id === caseRow.case_id ? 'selected-row' : ''}
                        key={caseRow.case_id}
                        onClick={() => selectCase(caseRow.case_id)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault()
                            selectCase(caseRow.case_id)
                          }
                        }}
                        role="button"
                        tabIndex={0}
                      >
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
                <h2>Defense Results</h2>
                <span>transaction and ring outcomes</span>
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

          {(view === 'command' || view === 'defense-lab' || view === 'experiments') && (
            <DefenseRationale run={run} />
          )}

          {view === 'defense-lab' && (
            <section className="panel">
              <div className="panel-header">
                <h2>Threshold Controls</h2>
                <span>alert budget model</span>
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
                  <span>alerts before budget cap</span>
                </div>
                <div className="control-result">
                  <strong>{Math.max(0, projectedAlerts - alertBudget)}</strong>
                  <span>expected backlog</span>
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
                <span>simulated groups</span>
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
                <h2>Run Memo</h2>
                <span>run summary</span>
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
                <h2>Benchmarks</h2>
                <span>available runs</span>
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
                <span>how this run is measured</span>
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
                The run uses generated accounts, merchants, instruments, transactions, cases, and
                labels. Labels are held back from the simulated review queue and used only to score
                the defenses. Drift changes model inputs inside the simulator; it does not describe
                real-world abuse methods.
              </p>
            </section>
          )}

          <LimitationsPanel />

          <p className="disclaimer" id="method">
            Demo data only. Do not use this project with real customer, payment, or case data.
            The simulator is for defensive evaluation, not guidance for abuse.
          </p>
        </section>
      </main>
      {selectedEvidence && (
        <EvidenceDrawer
          run={run}
          selection={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
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

function ScenarioSelector({
  scenarios,
  selectedScenario,
  value,
  onChange
}: {
  scenarios: ReturnType<typeof scenarioRows>
  selectedScenario: ReturnType<typeof scenarioRows>[number]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <section className="scenario-panel" aria-label="Scenario selector">
      <label>
        Scenario
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          {scenarios.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>{scenario.name}</option>
          ))}
        </select>
      </label>
      <div>
        <strong>{selectedScenario.question}</strong>
        <span>{selectedScenario.readout}</span>
      </div>
      <dl>
        <div>
          <dt>{selectedScenario.metricLabel}</dt>
          <dd>{selectedScenario.metric}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{selectedScenario.status}</dd>
        </div>
      </dl>
    </section>
  )
}

function DefenseRationale({ run }: { run: Run }) {
  const winner = winningDefense(run.defense_comparison)
  const maxAlerts = Math.max(...run.defense_comparison.map((row) => row.alerts), 1)
  return (
    <section className="panel rationale-panel" id="defense-rationale">
      <div className="panel-header">
        <h2>Why this defense won</h2>
        <span>{winner.defense.replaceAll('_', ' ')}</span>
      </div>
      <div className="rationale-grid">
        <div className="rationale-copy">
          <strong>{winner.defense.replaceAll('_', ' ')}</strong>
          <span>
            Best combined result in this run after weighting ring recall, transaction recall,
            precision, and alert load. A higher alert count is penalized because review capacity
            is part of the benchmark.
          </span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Defense</th>
                <th>Recall</th>
                <th>Ring recall</th>
                <th>Precision</th>
                <th>Alerts</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {run.defense_comparison.map((row) => (
                <tr className={row.defense === winner.defense ? 'selected-row' : ''} key={row.defense}>
                  <td>{row.defense.replaceAll('_', ' ')}</td>
                  <td>{pct(row.recall)}</td>
                  <td>{pct(row.ring_level_recall)}</td>
                  <td>{pct(row.precision)}</td>
                  <td>{row.alerts}</td>
                  <td>{defenseScore(row, maxAlerts).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function LimitationsPanel() {
  return (
    <section className="panel limitations-panel">
      <div className="panel-header">
        <h2>Limitations</h2>
        <span>what this run can and cannot prove</span>
      </div>
      <div className="limitations-list">
        <p>Synthetic behavior is useful for system testing, but it is not calibrated to a bank, card network, marketplace, or payment processor.</p>
        <p>Labels are generated ground truth. They are held back from the simulated review queue and used only for scoring.</p>
        <p>The graph shows bounded evidence from the generated run. It does not contain real customer, merchant, payment, device, or case data.</p>
        <p>Results compare defenses inside this simulator. They should not be read as claims about real-world fraud prevention.</p>
      </div>
    </section>
  )
}

function EvidenceDrawer({
  run,
  selection,
  onClose
}: {
  run: Run
  selection: EvidenceSelection
  onClose: () => void
}) {
  const record = buildEvidenceRecord(run, selection)
  return (
    <aside className="evidence-drawer" aria-label="Evidence detail">
      <div className="drawer-header">
        <div>
          <h2>{record.title}</h2>
          <span>{record.subtitle}</span>
        </div>
        <button aria-label="Close evidence detail" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>
      <dl className="drawer-metrics">
        {record.metrics.map((metric) => (
          <div key={metric.label}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
      <div className="drawer-section">
        <h3>Linked Evidence</h3>
        {record.sections.map((section) => (
          <div className="evidence-list" key={section.label}>
            <strong>{section.label}</strong>
            <span>{section.items.length ? section.items.join(', ') : 'none in current run'}</span>
          </div>
        ))}
      </div>
      <div className="drawer-section">
        <h3>Recent Events</h3>
        {record.events.length ? record.events.map((event) => (
          <p key={`${event.day}-${event.title}`}>D{event.day}: {event.title} - {event.detail}</p>
        )) : <p>No matching events in the sampled timeline.</p>}
      </div>
      {record.note && (
        <div className="drawer-note">
          <strong>Note</strong>
          <span>{record.note}</span>
        </div>
      )}
    </aside>
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

function scenarioRows(run: Run) {
  const graphDefense = run.defense_comparison.find((row) => row.defense.includes('graph'))
  const supervised = run.defense_comparison.find((row) => row.defense.includes('supervised'))
  const rules = run.defense_comparison.find((row) => row.defense.includes('rules'))
  return [
    {
      id: 'static-vs-adaptive',
      name: 'Static vs adaptive',
      question: 'How much recall is lost after behavior changes?',
      readout: `${pct(run.metrics.adversarial.recall_decay)} recall decay after synthetic friction.`,
      metricLabel: 'Half-life',
      metric: `${run.metrics.adversarial.adversarial_half_life} days`,
      status: 'current run'
    },
    {
      id: 'graph-vs-transaction',
      name: 'Graph vs transaction',
      question: 'Does graph context improve ring discovery?',
      readout: `Graph recall ${pct(graphDefense?.ring_level_recall ?? 0)} vs transaction recall ${pct(supervised?.ring_level_recall ?? 0)}.`,
      metricLabel: 'Graph alerts',
      metric: compact(graphDefense?.alerts ?? 0),
      status: 'implemented'
    },
    {
      id: 'investigator-overload',
      name: 'Recall vs overload',
      question: 'Where does extra recall turn into review pressure?',
      readout: `${compact(run.metrics.operations.backlog)} cases remain after the simulated review window.`,
      metricLabel: 'SLA missed',
      metric: compact(run.metrics.operations.sla_missed ?? 0),
      status: 'implemented'
    },
    {
      id: 'ring-priority',
      name: 'Ring-priority review',
      question: 'Does linked review return more per hour?',
      readout: `${money(run.metrics.financial.investigator_roi)} saved per investigator-hour in this run.`,
      metricLabel: 'Ring recall',
      metric: pct(run.metrics.graph.ring_level_recall),
      status: 'implemented'
    },
    {
      id: 'rules-baseline',
      name: 'Rules baseline',
      question: 'What does a simple rules pass miss?',
      readout: `Rules raised ${compact(rules?.alerts ?? 0)} alerts with ${pct(rules?.recall ?? 0)} transaction recall.`,
      metricLabel: 'Precision',
      metric: pct(rules?.precision ?? 0),
      status: 'implemented'
    }
  ]
}

function winningDefense(defenses: Run['defense_comparison'][number][]) {
  const maxAlerts = Math.max(...defenses.map((row) => row.alerts), 1)
  return [...defenses].sort((a, b) => defenseScore(b, maxAlerts) - defenseScore(a, maxAlerts))[0]
}

function defenseScore(row: Run['defense_comparison'][number], maxAlerts: number) {
  return row.ring_level_recall * 0.42
    + row.recall * 0.26
    + row.precision * 0.22
    - (row.alerts / maxAlerts) * 0.1
}

function buildEvidenceRecord(run: Run, selection: EvidenceSelection) {
  const node = run.graph.nodes.find((item) => item.id === selection.id)
  const caseRow = selection.kind === 'case'
    ? run.cases.find((item) => item.case_id === selection.id)
    : run.cases.find((item) => item.case_id === selection.id)
  const ring = findRingForSelection(run, selection.id, node, caseRow)
  const linked = linkedEvidence(run, selection.id, ring, caseRow)
  const events = matchingEvents(run, selection.id, ring?.ring_id).slice(0, 5)

  if (caseRow) {
    return {
      title: caseRow.case_id,
      subtitle: caseRow.ring_id ? `Case linked to ${caseRow.ring_id}` : 'Case without ring link',
      metrics: [
        { label: 'Priority', value: pct(caseRow.priority_score) },
        { label: 'Exposure', value: money(caseRow.dollar_exposure) },
        { label: 'False-positive risk', value: pct(caseRow.false_positive_risk ?? 0) },
        { label: 'Review time', value: `${caseRow.review_hours ?? 0} hr` }
      ],
      sections: [
        { label: 'Accounts', items: shortList(caseRow.account_ids ?? linked.accounts) },
        { label: 'Merchants', items: shortList(caseRow.merchant_ids ?? linked.merchants) },
        { label: 'Alerts', items: shortList(caseRow.alert_ids ?? []) },
        { label: 'Related nodes', items: shortList(linked.neighbors) }
      ],
      events,
      note: caseRow.notes || caseRow.recommended_action
    }
  }

  return {
    title: selection.id,
    subtitle: node ? `${node.type.replaceAll('_', ' ')} evidence node` : 'Evidence node',
    metrics: [
      { label: 'Type', value: node?.type.replaceAll('_', ' ') ?? 'unknown' },
      { label: 'Ring', value: ring?.ring_id ?? node?.ring_id ?? 'none' },
      { label: 'Links', value: compact(linked.neighbors.length) },
      { label: 'Cases', value: compact(linked.cases.length) }
    ],
    sections: [
      { label: 'Accounts', items: shortList(linked.accounts) },
      { label: 'Merchants', items: shortList(linked.merchants) },
      { label: 'Devices / IPs', items: shortList([...linked.devices, ...linked.ips]) },
      { label: 'Cases', items: shortList(linked.cases) }
    ],
    events,
    note: ring?.detection_memory?.[0] ?? 'Evidence is generated from the local synthetic run.'
  }
}

function findRingForSelection(
  run: Run,
  id: string,
  node?: Run['graph']['nodes'][number],
  caseRow?: Run['cases'][number]
) {
  if (caseRow?.ring_id) {
    return run.rings.find((ring) => ring.ring_id === caseRow.ring_id)
  }
  if (node?.type === 'ring') {
    return run.rings.find((ring) => ring.ring_id === id)
  }
  if (node?.ring_id) {
    return run.rings.find((ring) => ring.ring_id === node.ring_id)
  }
  return run.rings.find((ring) => ring.members.includes(id) || ring.merchants.includes(id))
}

function linkedEvidence(
  run: Run,
  id: string,
  ring?: Run['rings'][number],
  caseRow?: Run['cases'][number]
) {
  const byId = new Map(run.graph.nodes.map((node) => [node.id, node]))
  const neighborIds = run.graph.edges
    .filter((edge) => edge.source === id || edge.target === id)
    .map((edge) => edge.source === id ? edge.target : edge.source)
  const neighbors = neighborIds.map((neighborId) => byId.get(neighborId)).filter(Boolean) as Run['graph']['nodes']
  const caseIds = new Set<string>()
  for (const item of run.cases) {
    if (item.case_id === id || item.ring_id === ring?.ring_id || item.account_ids?.includes(id)) {
      caseIds.add(item.case_id)
    }
  }
  return {
    neighbors: neighborIds,
    accounts: unique([
      ...(caseRow?.account_ids ?? []),
      ...(ring?.members ?? []),
      ...neighbors.filter((node) => node.type === 'account').map((node) => node.id)
    ]),
    merchants: unique([
      ...(caseRow?.merchant_ids ?? []),
      ...(ring?.merchants ?? []),
      ...neighbors.filter((node) => node.type === 'merchant').map((node) => node.id)
    ]),
    devices: unique([
      ...(ring?.shared_devices ?? []),
      ...neighbors.filter((node) => node.type === 'device' || node.type === 'payment_instrument').map((node) => node.id)
    ]),
    ips: unique([
      ...(ring?.shared_ip_clusters ?? []),
      ...neighbors.filter((node) => node.type === 'ip_cluster').map((node) => node.id)
    ]),
    cases: [...caseIds]
  }
}

function matchingEvents(run: Run, id: string, ringId?: string) {
  return run.timeline.filter((event) => {
    const text = `${event.title} ${event.detail}`
    return text.includes(id) || Boolean(ringId && text.includes(ringId))
  })
}

function unique(items: string[]) {
  return [...new Set(items.filter(Boolean))]
}

function shortList(items: string[]) {
  return items.slice(0, 8)
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
    battlefield: 'Evidence Map',
    rings: 'Rings',
    cases: 'Cases',
    experiments: 'Experiments',
    'defense-lab': 'Defense Tests',
    'after-action': 'Run Memo',
    methodology: 'Methodology'
  }
  return titles[view]
}

function experimentRows() {
  return [
    {
      name: 'Static Fraud vs Adaptive Fraud',
      question: 'How much recall is lost after drift?',
      status: 'implemented'
    },
    {
      name: 'Transaction Model vs Graph Model',
      question: 'Does graph context improve ring discovery?',
      status: 'implemented'
    },
    {
      name: 'Recall vs Investigator Overload',
      question: 'Where does added recall overload review?',
      status: 'implemented'
    },
    {
      name: 'Ring Takedown vs Account Takedown',
      question: 'Does group review return more per hour?',
      status: 'implemented'
    },
    {
      name: 'Active Learning Under Drift',
      question: 'Do review labels help after drift?',
      status: 'implemented'
    },
    {
      name: 'Adaptive Thresholding',
      question: 'Can thresholds keep the queue usable?',
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
