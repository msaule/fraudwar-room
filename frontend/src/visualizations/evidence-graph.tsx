'use client'

import { useEffect, useMemo, useState } from 'react'
import { Background, Controls, ReactFlow, type Edge, type Node } from '@xyflow/react'

type Graph = {
  nodes: Array<{ id: string; label: string; type: string; ring_id?: string | null }>
  edges: Array<{ source: string; target: string; type: string }>
}

export function EvidenceGraph({ graph }: { graph: Graph }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const { nodes, edges } = useMemo(() => {
    const displayed = selectEvidenceNodes(graph)
    const laneCounts = new Map<string, number>()
    const nodes: Node[] = displayed.map((node) => {
      const lane = laneForType(node.type)
      const row = laneCounts.get(lane) ?? 0
      laneCounts.set(lane, row + 1)
      const laneSize = displayed.filter((item) => laneForType(item.type) === lane).length
      return {
        id: node.id,
        data: { label: shortLabel(node.id, node.type) },
        position: {
          x: laneX(lane),
          y: laneY(row, laneSize, lane)
        },
        type: 'default',
        className: `${node.type} lane-${lane}`,
        draggable: true,
        style: { width: node.type === 'account' ? 122 : 136 }
      }
    })
    const included = new Set(nodes.map((node) => node.id))
    const edges: Edge[] = graph.edges
      .filter((edge) => included.has(edge.source) && included.has(edge.target))
      .slice(0, 120)
      .map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        animated: edge.type.includes('case') || edge.type.includes('ring'),
        type: 'smoothstep',
        className: edgeClass(edge.type)
      }))
    return { nodes, edges }
  }, [graph])

  if (!mounted) {
    return <div aria-label="Loading graph evidence" />
  }

  return (
    <div className="evidence-map">
      <div className="graph-legend" aria-label="Evidence map lanes">
        <span>Rings</span>
        <span>Cases</span>
        <span>Accounts</span>
        <span>Counterparties</span>
        <span>Activity</span>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.25}
        maxZoom={1.55}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#242b35" gap={24} />
        <Controls />
      </ReactFlow>
    </div>
  )
}

function selectEvidenceNodes(graph: Graph) {
  const byId = new Map(graph.nodes.map((node) => [node.id, node]))
  const selected = new Set<string>()
  const limits: Record<string, number> = {
    ring: 4,
    case: 7,
    account: 14,
    merchant: 7,
    payment_instrument: 5,
    device: 5,
    ip_cluster: 5,
    transaction: 8,
    refund: 3,
    chargeback: 3,
    dispute: 3,
    support_contact: 2,
    account_change: 2
  }

  for (const node of graph.nodes) {
    if (node.type === 'ring' || node.type === 'case') {
      selected.add(node.id)
    }
  }

  addLinkedNodes(graph, byId, selected, 'account', limits.account)
  addLinkedNodes(graph, byId, selected, 'merchant', limits.merchant)
  addLinkedNodes(graph, byId, selected, 'payment_instrument', limits.payment_instrument)
  addLinkedNodes(graph, byId, selected, 'device', limits.device)
  addLinkedNodes(graph, byId, selected, 'ip_cluster', limits.ip_cluster)
  addLinkedNodes(graph, byId, selected, 'transaction', limits.transaction)
  addLinkedNodes(graph, byId, selected, 'refund', limits.refund)
  addLinkedNodes(graph, byId, selected, 'chargeback', limits.chargeback)
  addLinkedNodes(graph, byId, selected, 'dispute', limits.dispute)
  addLinkedNodes(graph, byId, selected, 'support_contact', limits.support_contact)
  addLinkedNodes(graph, byId, selected, 'account_change', limits.account_change)

  return graph.nodes.filter((node) => selected.has(node.id)).sort(sortForMap)
}

function addLinkedNodes(
  graph: Graph,
  byId: Map<string, Graph['nodes'][number]>,
  selected: Set<string>,
  type: string,
  limit: number
) {
  const candidates: string[] = []
  for (const edge of graph.edges) {
    const sourceSelected = selected.has(edge.source)
    const targetSelected = selected.has(edge.target)
    const source = byId.get(edge.source)
    const target = byId.get(edge.target)
    if (sourceSelected && target?.type === type) {
      candidates.push(target.id)
    }
    if (targetSelected && source?.type === type) {
      candidates.push(source.id)
    }
  }
  for (const id of [...new Set(candidates)].slice(0, limit)) {
    selected.add(id)
  }
}

function sortForMap(a: Graph['nodes'][number], b: Graph['nodes'][number]) {
  const laneDiff = laneOrder(laneForType(a.type)) - laneOrder(laneForType(b.type))
  if (laneDiff) {
    return laneDiff
  }
  return a.id.localeCompare(b.id)
}

function laneForType(type: string) {
  if (type === 'ring') return 'rings'
  if (type === 'case') return 'cases'
  if (type === 'account') return 'accounts'
  if (['merchant', 'payment_instrument', 'device', 'ip_cluster'].includes(type)) return 'counterparties'
  return 'activity'
}

function laneOrder(lane: string) {
  return ['rings', 'cases', 'accounts', 'counterparties', 'activity'].indexOf(lane)
}

function laneX(lane: string) {
  return {
    rings: 0,
    cases: 170,
    accounts: 340,
    counterparties: 530,
    activity: 720
  }[lane] ?? 0
}

function laneY(row: number, laneSize: number, lane: string) {
  const spacing = lane === 'accounts' ? 52 : 58
  const start = Math.max(0, 260 - ((laneSize - 1) * spacing) / 2)
  return start + row * spacing
}

function shortLabel(id: string, type: string) {
  if (type === 'account') return id.replace('acct_', 'acct ')
  if (type === 'merchant') return id.replace('merch_', 'm ')
  if (type === 'transaction') return id.replace('txn_', 'txn ')
  if (type === 'payment_instrument') return id.replace('pi_', 'pi ').slice(0, 18)
  if (type === 'support_contact') return id.replace('support_', 'support ')
  if (type === 'account_change') return id.replace('acct_change_', 'change ')
  return id.replaceAll('_', ' ')
}

function edgeClass(type: string) {
  if (type.includes('ring')) return 'edge-ring'
  if (type.includes('case')) return 'edge-case'
  if (type.includes('device') || type.includes('ip') || type.includes('payment')) return 'edge-infra'
  return 'edge-standard'
}
