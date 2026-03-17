import { MarkerType, type Node, type Edge } from '@xyflow/react';
import type { FlowDefinition, FlowStep } from '../types/flow';
import { agentRegistry } from './agentRegistry';

const NODE_X = 250;
const NODE_Y_START = 120;
const NODE_Y_GAP = 150;
export const START_NODE_ID = 'start';

let nodeIdCounter = 0;

export function getNextNodeId(): string {
  return `node_${++nodeIdCounter}`;
}

export function resetNodeIdCounter(value = 0): void {
  nodeIdCounter = value;
}

export interface AgentNodeData {
  agent: string;
  arguments: Record<string, unknown>;
  color: string;
  description: string;
  [key: string]: unknown;
}

export function createStartNode(x = NODE_X + 50, y = 20): Node {
  return {
    id: START_NODE_ID,
    type: 'startNode',
    position: { x, y },
    data: {},
    deletable: false,
  };
}

export function flowToNodes(flow: FlowDefinition): { nodes: Node[]; edges: Edge[] } {
  resetNodeIdCounter();

  const startNode = createStartNode();
  const agentNodes: Node[] = flow.steps.map((step, index) => {
    const id = getNextNodeId();
    const meta = agentRegistry[step.agent];
    const nodeType = meta?.category === 'judgment' ? 'judgmentNode' : 'agentNode';
    return {
      id,
      type: nodeType,
      position: { x: NODE_X, y: NODE_Y_START + index * NODE_Y_GAP },
      data: {
        agent: step.agent,
        arguments: step.arguments || {},
        color: meta?.color || '#999',
        description: meta?.description || '',
      } satisfies AgentNodeData,
    };
  });

  const nodes = [startNode, ...agentNodes];

  const marker = { type: MarkerType.ArrowClosed, width: 16, height: 16 };
  const edges: Edge[] = [];
  if (agentNodes.length > 0) {
    edges.push({
      id: `edge_${START_NODE_ID}_${agentNodes[0].id}`,
      source: START_NODE_ID,
      target: agentNodes[0].id,
      type: 'smoothstep',
      animated: true,
      markerEnd: marker,
    });
  }
  for (let i = 0; i < agentNodes.length - 1; i++) {
    edges.push({
      id: `edge_${agentNodes[i].id}_${agentNodes[i + 1].id}`,
      source: agentNodes[i].id,
      target: agentNodes[i + 1].id,
      type: 'smoothstep',
      animated: true,
      markerEnd: marker,
    });
  }

  return { nodes, edges };
}

export function nodesToFlow(
  nodes: Node[],
  edges: Edge[],
  meta: { name: string; description: string; command: string },
): FlowDefinition {
  const agentNodes = nodes.filter(n => n.type === 'agentNode' || n.type === 'judgmentNode');
  const ordered = topologicalSortFromStart(agentNodes, edges);

  const steps: FlowStep[] = ordered.map(node => {
    const data = node.data as AgentNodeData;
    return {
      agent: data.agent,
      arguments: data.arguments || {},
    };
  });

  return {
    name: meta.name,
    description: meta.description,
    command: meta.command,
    steps,
  };
}

/**
 * Start ノードから BFS でエッジを辿り、DAG のトポロジカル順序でノードを返す。
 * エッジの source/target は接続時の方向をそのまま使う（Start からの到達順）。
 */
function topologicalSortFromStart(agentNodes: Node[], edges: Edge[]): Node[] {
  if (agentNodes.length === 0) return [];

  const nodeMap = new Map(agentNodes.map(n => [n.id, n]));

  // 隣接リスト構築（source → target[]）
  const adj = new Map<string, string[]>();
  const inDegree = new Map<string, number>();

  for (const node of agentNodes) {
    adj.set(node.id, []);
    inDegree.set(node.id, 0);
  }
  // Start ノードも含める
  adj.set(START_NODE_ID, []);

  for (const edge of edges) {
    const targets = adj.get(edge.source);
    if (targets) {
      targets.push(edge.target);
    }
    if (inDegree.has(edge.target)) {
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    }
  }

  // Start ノードから到達可能なノードの入次数を減算
  const startTargets = adj.get(START_NODE_ID) || [];
  for (const t of startTargets) {
    if (inDegree.has(t)) {
      inDegree.set(t, (inDegree.get(t) || 0) - 1);
    }
  }

  // BFS (Kahn's algorithm) — 入次数0のノードから開始
  const queue: string[] = [];
  for (const [id, deg] of inDegree) {
    if (deg <= 0 && startTargets.includes(id)) {
      queue.push(id);
    }
  }

  // Start から直接つながっていないが入次数0のノードも追加
  for (const [id, deg] of inDegree) {
    if (deg <= 0 && !queue.includes(id)) {
      queue.push(id);
    }
  }

  const ordered: Node[] = [];
  const visited = new Set<string>();

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current)) continue;
    visited.add(current);

    const node = nodeMap.get(current);
    if (node) ordered.push(node);

    for (const next of adj.get(current) || []) {
      if (visited.has(next)) continue;
      const deg = (inDegree.get(next) || 0) - 1;
      inDegree.set(next, deg);
      if (deg <= 0) {
        queue.push(next);
      }
    }
  }

  // DAG に含まれなかったノードをフォールバック追加
  const remaining = agentNodes
    .filter(n => !visited.has(n.id))
    .sort((a, b) => a.position.y - b.position.y);
  ordered.push(...remaining);

  return ordered;
}
