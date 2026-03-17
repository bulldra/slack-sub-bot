import { useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  MarkerType,
  reconnectEdge,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type Connection,
  type EdgeMouseHandler,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode, StartNode, JudgmentNode } from './AgentNode';
import { agentRegistry } from '../utils/agentRegistry';
import { getNextNodeId, START_NODE_ID, type AgentNodeData } from '../utils/yamlConverter';

const nodeTypes = { agentNode: AgentNode, startNode: StartNode, judgmentNode: JudgmentNode };

const defaultEdgeOptions = {
  style: { stroke: '#94a3b8', strokeWidth: 1.5 },
  type: 'smoothstep' as const,
  animated: true,
  markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: '#94a3b8' },
};

interface FlowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
  onNodeSelect: (node: Node | null) => void;
}

/**
 * Start ノードから BFS で到達順（深さ）を算出し、
 * エッジの向きを「深さが浅い → 深い」に正規化する。
 */
function normalizeEdgeDirections(edges: Edge[]): Edge[] {
  // 無向隣接リスト構築
  const adj = new Map<string, Set<string>>();
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, new Set());
    if (!adj.has(e.target)) adj.set(e.target, new Set());
    adj.get(e.source)!.add(e.target);
    adj.get(e.target)!.add(e.source);
  }

  // BFS で Start からの深さを算出
  const depth = new Map<string, number>();
  depth.set(START_NODE_ID, 0);
  const queue = [START_NODE_ID];
  while (queue.length > 0) {
    const current = queue.shift()!;
    const d = depth.get(current)!;
    for (const neighbor of adj.get(current) || []) {
      if (!depth.has(neighbor)) {
        depth.set(neighbor, d + 1);
        queue.push(neighbor);
      }
    }
  }

  return edges.map(e => {
    const dSource = depth.get(e.source) ?? Infinity;
    const dTarget = depth.get(e.target) ?? Infinity;

    // source が target より深い場合は反転
    if (dSource > dTarget) {
      return {
        ...e,
        id: `edge_${e.target}_${e.source}`,
        source: e.target,
        target: e.source,
        sourceHandle: e.targetHandle,
        targetHandle: e.sourceHandle,
        type: 'smoothstep',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
      };
    }

    return {
      ...e,
      type: 'smoothstep',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    };
  });
}

export function FlowCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  setNodes,
  setEdges,
  onNodeSelect,
}: FlowCanvasProps) {
  const { screenToFlowPosition } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges(eds => {
        // 重複エッジ防止
        const exists = eds.some(
          e =>
            (e.source === params.source && e.target === params.target) ||
            (e.source === params.target && e.target === params.source),
        );
        if (exists) return eds;

        const newEdge: Edge = {
          id: `edge_${params.source}_${params.target}`,
          source: params.source!,
          target: params.target!,
          sourceHandle: params.sourceHandle,
          targetHandle: params.targetHandle,
          type: 'smoothstep',
          animated: true,
        };

        return normalizeEdgeDirections([...eds, newEdge]);
      });
    },
    [setEdges],
  );

  const onReconnect = useCallback(
    (oldEdge: Edge, newConnection: Connection) => {
      setEdges(eds => {
        const updated = reconnectEdge(oldEdge, newConnection, eds);
        return normalizeEdgeDirections(updated);
      });
    },
    [setEdges],
  );

  const onEdgeClick: EdgeMouseHandler = useCallback(
    (_event, edge) => {
      // エッジ選択時にselectedをトグル（Delete キーで削除可能にする）
      setEdges(eds =>
        eds.map(e => ({
          ...e,
          selected: e.id === edge.id ? !e.selected : false,
        })),
      );
    },
    [setEdges],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const agentName = event.dataTransfer.getData('application/agentflow');
      if (!agentName) return;

      const meta = agentRegistry[agentName];
      if (!meta) return;

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const nodeType = meta.category === 'judgment' ? 'judgmentNode' : 'agentNode';

      const newNode: Node = {
        id: getNextNodeId(),
        type: nodeType,
        position,
        data: {
          agent: agentName,
          arguments: { ...meta.defaultArguments },
          color: meta.color,
          description: meta.description,
        } satisfies AgentNodeData,
      };

      setNodes(nds => [...nds, newNode]);
    },
    [screenToFlowPosition, setNodes],
  );

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeSelect(node);
    },
    [onNodeSelect],
  );

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  // 表示時に常に正規化された方向 + 矢印を適用
  const normalizedEdges = normalizeEdgeDirections(edges);

  return (
    <div style={{ flex: 1, height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={normalizedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onReconnect={onReconnect}
        onEdgeClick={onEdgeClick}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        edgesReconnectable
        fitView
        deleteKeyCode="Delete"
        style={{ background: '#f8fafc' }}
      >
        <Controls
          style={{
            borderRadius: 8,
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            border: '1px solid #e2e8f0',
          }}
        />
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#cbd5e1" />
      </ReactFlow>
    </div>
  );
}
