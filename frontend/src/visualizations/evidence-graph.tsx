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
    const displayed = graph.nodes.slice(0, 90)
    const radius = 190
    const centerX = 390
    const centerY = 235
    const nodes: Node[] = displayed.map((node, index) => {
      const angle = (index / Math.max(displayed.length, 1)) * Math.PI * 2
      const inner = node.type === 'ring' ? 0 : 1
      const r = node.type === 'account' ? radius : radius * 0.66 + inner * 25
      return {
        id: node.id,
        data: { label: node.id.replace('acct_', 'a_').replace('merch_', 'm_') },
        position: {
          x: centerX + Math.cos(angle) * r,
          y: centerY + Math.sin(angle) * r
        },
        type: 'default',
        className: node.type,
        draggable: true
      }
    })
    const included = new Set(nodes.map((node) => node.id))
    const edges: Edge[] = graph.edges
      .filter((edge) => included.has(edge.source) && included.has(edge.target))
      .slice(0, 160)
      .map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        animated: edge.type.includes('ring'),
        label: edge.type.includes('ring') ? edge.type : undefined
      }))
    return { nodes, edges }
  }, [graph])

  if (!mounted) {
    return <div aria-label="Loading graph evidence" />
  }

  return (
    <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.35} maxZoom={1.8}>
      <Background color="#242b35" />
      <Controls />
    </ReactFlow>
  )
}
