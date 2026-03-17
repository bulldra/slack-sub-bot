import { useMemo, useState } from 'react';
import type { FlowListItem } from '../types/flow';
import { agentRegistry, type AgentCategory } from '../utils/agentRegistry';

interface SidebarProps {
  flowList: FlowListItem[];
  selectedFlowName: string | null;
  onSelectFlow: (name: string) => void;
  onNewFlow: () => void;
}

const categoryLabels: Record<AgentCategory, string> = {
  judgment: 'Judgment',
  input: 'Input',
  processing: 'Processing',
  output: 'Output',
  utility: 'Utility',
};

const categoryIcons: Record<AgentCategory, string> = {
  judgment: '\u2753',
  input: '\u{1F4E5}',
  processing: '\u2699\uFE0F',
  output: '\u{1F4E4}',
  utility: '\u{1F527}',
};

const categoryOrder: AgentCategory[] = ['judgment', 'input', 'processing', 'output', 'utility'];

export function Sidebar({ flowList, selectedFlowName, onSelectFlow, onNewFlow }: SidebarProps) {
  const [hoveredFlow, setHoveredFlow] = useState<string | null>(null);
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);

  const groupedAgents = useMemo(() => {
    const groups: Record<AgentCategory, { key: string; meta: typeof agentRegistry[string] }[]> = {
      judgment: [],
      input: [],
      processing: [],
      output: [],
      utility: [],
    };
    for (const [key, meta] of Object.entries(agentRegistry)) {
      groups[meta.category].push({ key, meta });
    }
    return groups;
  }, []);

  const onDragStart = (event: React.DragEvent, agentKey: string) => {
    event.dataTransfer.setData('application/agentflow', agentKey);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      style={{
        width: 280,
        borderRight: '1px solid #e2e8f0',
        display: 'flex',
        flexDirection: 'column',
        background: '#f8fafc',
        overflow: 'hidden',
      }}
    >
      {/* Flow List */}
      <div style={{ background: '#fff', borderBottom: '2px solid #e2e8f0' }}>
        <div style={{ padding: '14px 16px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Flows
          </h3>
          <button
            onClick={onNewFlow}
            style={{
              padding: '5px 12px',
              fontSize: 12,
              fontWeight: 600,
              border: 'none',
              borderRadius: 6,
              background: '#3b82f6',
              color: '#fff',
              cursor: 'pointer',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = '#2563eb')}
            onMouseLeave={e => (e.currentTarget.style.background = '#3b82f6')}
          >
            + New
          </button>
        </div>
        <div style={{ maxHeight: 200, overflowY: 'auto', padding: '0 8px 8px' }}>
          {flowList.map(flow => {
            const isSelected = selectedFlowName === flow.name;
            const isHovered = hoveredFlow === flow.name;
            return (
              <div
                key={flow.name}
                onClick={() => onSelectFlow(flow.name)}
                onMouseEnter={() => setHoveredFlow(flow.name)}
                onMouseLeave={() => setHoveredFlow(null)}
                style={{
                  padding: '8px 12px',
                  marginBottom: 2,
                  borderRadius: 8,
                  cursor: 'pointer',
                  background: isSelected ? '#eff6ff' : isHovered ? '#f8fafc' : 'transparent',
                  borderLeft: isSelected ? '3px solid #3b82f6' : '3px solid transparent',
                  fontSize: 13,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 500, color: isSelected ? '#1d4ed8' : '#1e293b' }}>
                  {flow.command}
                </div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                  {flow.description} ({flow.stepCount} steps)
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Agent Palette */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px' }}>
        <h3 style={{ margin: '0 4px 10px', fontSize: 13, fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Agents
        </h3>
        {categoryOrder.map(category => (
          <div key={category} style={{ marginBottom: 16 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: '#94a3b8',
                textTransform: 'uppercase',
                marginBottom: 6,
                padding: '0 4px',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                letterSpacing: 0.5,
              }}
            >
              <span style={{ fontSize: 12 }}>{categoryIcons[category]}</span>
              {categoryLabels[category]}
            </div>
            {groupedAgents[category].map(({ key, meta }) => {
              const isHovered = hoveredAgent === key;
              return (
                <div
                  key={key}
                  draggable
                  onDragStart={e => onDragStart(e, key)}
                  onMouseEnter={() => setHoveredAgent(key)}
                  onMouseLeave={() => setHoveredAgent(null)}
                  style={{
                    padding: '8px 12px',
                    marginBottom: 3,
                    borderRadius: 8,
                    borderLeft: `3px solid ${meta.color}`,
                    background: '#fff',
                    cursor: 'grab',
                    fontSize: 12,
                    boxShadow: isHovered
                      ? '0 2px 8px rgba(0,0,0,0.08)'
                      : '0 1px 2px rgba(0,0,0,0.04)',
                    transition: 'box-shadow 0.15s ease, transform 0.1s ease',
                    transform: isHovered ? 'translateX(2px)' : 'none',
                  }}
                >
                  <div style={{ fontWeight: 500, color: '#1e293b' }}>{meta.name}</div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>{meta.description}</div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
