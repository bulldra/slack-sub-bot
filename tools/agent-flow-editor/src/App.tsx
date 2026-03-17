import { useState, useEffect, useCallback } from 'react';
import { ReactFlowProvider, useNodesState, useEdgesState, type Node, type Edge } from '@xyflow/react';
import { FlowCanvas } from './components/FlowCanvas';
import { Sidebar } from './components/Sidebar';
import { ArgumentEditor } from './components/ArgumentEditor';
import { FlowToolbar } from './components/FlowToolbar';
import { useFlowApi } from './hooks/useFlowApi';
import { flowToNodes, nodesToFlow, resetNodeIdCounter, createStartNode, type AgentNodeData } from './utils/yamlConverter';

function FlowEditor() {
  const { flowList, loading, fetchFlowList, fetchFlow, saveFlow, deleteFlow, fetchAgents } = useFlowApi();

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([] as Edge[]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const [flowName, setFlowName] = useState('');
  const [flowDescription, setFlowDescription] = useState('');
  const [flowCommand, setFlowCommand] = useState('');
  const [selectedFlowName, setSelectedFlowName] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchFlowList();
    fetchAgents();
  }, [fetchFlowList, fetchAgents]);

  useEffect(() => {
    setHasUnsavedChanges(true);
  }, [nodes, edges, flowName, flowDescription, flowCommand]);

  const handleSelectFlow = useCallback(
    async (name: string) => {
      const flow = await fetchFlow(name);
      if (!flow) return;

      const { nodes: newNodes, edges: newEdges } = flowToNodes(flow);
      setNodes(newNodes);
      setEdges(newEdges);
      setFlowName(flow.name);
      setFlowDescription(flow.description);
      setFlowCommand(flow.command);
      setSelectedFlowName(name);
      setSelectedNode(null);
      setHasUnsavedChanges(false);
    },
    [fetchFlow, setNodes, setEdges],
  );

  const handleNewFlow = useCallback(() => {
    resetNodeIdCounter();
    setNodes([createStartNode()]);
    setEdges([]);
    setFlowName('');
    setFlowDescription('');
    setFlowCommand('');
    setSelectedFlowName(null);
    setSelectedNode(null);
    setHasUnsavedChanges(false);
  }, [setNodes, setEdges]);

  const handleSave = useCallback(async () => {
    if (!flowName) return;
    setSaving(true);
    const flow = nodesToFlow(nodes, edges, {
      name: flowName,
      description: flowDescription,
      command: flowCommand,
    });
    const success = await saveFlow(flowName, flow);
    if (success) {
      setSelectedFlowName(flowName);
      setHasUnsavedChanges(false);
      await fetchFlowList();
    }
    setSaving(false);
  }, [flowName, flowDescription, flowCommand, nodes, edges, saveFlow, fetchFlowList]);

  const handleDelete = useCallback(async () => {
    if (!selectedFlowName) return;
    const success = await deleteFlow(selectedFlowName);
    if (success) {
      handleNewFlow();
      await fetchFlowList();
    }
  }, [selectedFlowName, deleteFlow, handleNewFlow, fetchFlowList]);

  const handleNodeSelect = useCallback(
    (node: Node | null) => {
      setSelectedNode(node);
    },
    [],
  );

  const handleUpdateNodeData = useCallback(
    (nodeId: string, args: Record<string, unknown>) => {
      setNodes(nds =>
        nds.map(n => {
          if (n.id === nodeId) {
            const data = n.data as AgentNodeData;
            return { ...n, data: { ...data, arguments: args } };
          }
          return n;
        }),
      );
    },
    [setNodes],
  );

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', background: '#f1f5f9', color: '#1e293b' }}>
      <FlowToolbar
        flowName={flowName}
        flowDescription={flowDescription}
        flowCommand={flowCommand}
        onFlowNameChange={setFlowName}
        onFlowDescriptionChange={setFlowDescription}
        onFlowCommandChange={setFlowCommand}
        onSave={handleSave}
        onDelete={handleDelete}
        saving={saving || loading}
        hasUnsavedChanges={hasUnsavedChanges}
      />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Sidebar
          flowList={flowList}
          selectedFlowName={selectedFlowName}
          onSelectFlow={handleSelectFlow}
          onNewFlow={handleNewFlow}
        />
        <FlowCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          setNodes={setNodes}
          setEdges={setEdges}
          onNodeSelect={handleNodeSelect}
        />
        <ArgumentEditor selectedNode={selectedNode} onUpdateNodeData={handleUpdateNodeData} />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowEditor />
    </ReactFlowProvider>
  );
}
