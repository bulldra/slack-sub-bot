import { memo, useState } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { AgentNodeData } from '../utils/yamlConverter';
import { agentRegistry } from '../utils/agentRegistry';

type AgentNodeProps = NodeProps & { data: AgentNodeData };

const handleStyle = () => ({
  background: 'transparent',
  border: 'none',
  width: 10,
  height: 10,
});

const categoryIcons: Record<string, string> = {
  judgment: '\u2753',
  input: '\u{1F4E5}',
  processing: '\u2699\uFE0F',
  output: '\u{1F4E4}',
  utility: '\u{1F527}',
};

function AgentNodeComponent({ data, selected }: AgentNodeProps) {
  const [hovered, setHovered] = useState(false);
  const [argsExpanded, setArgsExpanded] = useState(false);
  const hasArgs = data.arguments && Object.keys(data.arguments).length > 0;
  const meta = agentRegistry[data.agent];
  const category = meta?.category ?? 'utility';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: '#fff',
        borderRadius: 10,
        borderLeft: `3px solid ${data.color}`,
        width: 160,
        boxShadow: selected
          ? `0 0 0 2px ${data.color}40, 0 4px 12px rgba(0,0,0,0.12)`
          : hovered
            ? '0 4px 12px rgba(0,0,0,0.12)'
            : '0 1px 3px rgba(0,0,0,0.08)',
        cursor: 'grab',
        transition: 'box-shadow 0.2s ease, transform 0.15s ease',
        transform: hovered ? 'translateY(-1px)' : 'none',
        overflow: 'hidden',
      }}
    >
      <Handle type="source" position={Position.Top} id="top" style={handleStyle()} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={handleStyle()} />
      <Handle type="source" position={Position.Left} id="left" style={handleStyle()} />
      <Handle type="source" position={Position.Right} id="right" style={handleStyle()} />
      <Handle type="target" position={Position.Top} id="target-top" style={handleStyle()} />
      <Handle type="target" position={Position.Bottom} id="target-bottom" style={handleStyle()} />
      <Handle type="target" position={Position.Left} id="target-left" style={handleStyle()} />
      <Handle type="target" position={Position.Right} id="target-right" style={handleStyle()} />

      {/* Header */}
      <div style={{ padding: '6px 8px 3px', display: 'flex', alignItems: 'center', gap: 5 }}>
        <span style={{ fontSize: 11 }}>{categoryIcons[category] || '\u{1F4E6}'}</span>
        <div style={{ fontWeight: 600, fontSize: 11, flex: 1, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {meta?.name ?? data.agent}
        </div>
        <span
          style={{
            fontSize: 8,
            fontWeight: 600,
            textTransform: 'uppercase',
            background: `${data.color}18`,
            color: data.color,
            padding: '1px 4px',
            borderRadius: 3,
            letterSpacing: 0.3,
            flexShrink: 0,
          }}
        >
          {category}
        </span>
      </div>

      {/* Description */}
      <div style={{ padding: '0 8px 5px', fontSize: 9, color: '#64748b', lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {data.description}
      </div>

      {/* Context I/O Tags */}
      {(meta?.contextInputs?.length || meta?.contextOutputs?.length) ? (
        <div style={{ padding: '3px 8px 4px', display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {meta?.contextInputs?.map((key) => (
            <span
              key={`in-${key}`}
              style={{
                fontSize: 7,
                fontWeight: 600,
                background: '#dbeafe',
                color: '#1d4ed8',
                padding: '1px 4px',
                borderRadius: 3,
                letterSpacing: 0.2,
                lineHeight: 1.4,
              }}
            >
              {'\u2193'} {key}
            </span>
          ))}
          {meta?.contextOutputs?.map((key) => (
            <span
              key={`out-${key}`}
              style={{
                fontSize: 7,
                fontWeight: 600,
                background: '#dcfce7',
                color: '#15803d',
                padding: '1px 4px',
                borderRadius: 3,
                letterSpacing: 0.2,
                lineHeight: 1.4,
              }}
            >
              {'\u2191'} {key}
            </span>
          ))}
        </div>
      ) : null}

      {/* Args (collapsible) */}
      {hasArgs && (
        <div style={{ borderTop: '1px solid #f1f5f9' }}>
          <div
            onClick={(e) => { e.stopPropagation(); setArgsExpanded(!argsExpanded); }}
            style={{
              padding: '2px 8px',
              fontSize: 8,
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 3,
              userSelect: 'none',
            }}
          >
            <span style={{ transform: argsExpanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s', display: 'inline-block', fontSize: 7 }}>
              {'\u25B6'}
            </span>
            {Object.keys(data.arguments).length} args
          </div>
          {argsExpanded && (
            <div
              style={{
                fontSize: 8,
                color: '#64748b',
                background: '#f8fafc',
                padding: '3px 8px 4px',
                fontFamily: '"SF Mono", "Fira Code", monospace',
                maxHeight: 50,
                overflow: 'auto',
              }}
            >
              {Object.entries(data.arguments).map(([key, val]) => (
                <div key={key} style={{ marginBottom: 1 }}>
                  <span style={{ color: '#94a3b8' }}>{key}:</span> {JSON.stringify(val)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);

function StartNodeComponent({ selected }: NodeProps) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'linear-gradient(135deg, #22c55e, #16a34a)',
        color: '#fff',
        borderRadius: 16,
        padding: '6px 18px',
        fontWeight: 700,
        fontSize: 11,
        letterSpacing: 0.3,
        boxShadow: selected
          ? '0 0 0 3px rgba(34,197,94,0.4), 0 4px 12px rgba(0,0,0,0.15)'
          : hovered
            ? '0 4px 12px rgba(0,0,0,0.15)'
            : '0 2px 6px rgba(0,0,0,0.12)',
        cursor: 'grab',
        transition: 'box-shadow 0.2s ease, transform 0.15s ease',
        transform: hovered ? 'translateY(-1px)' : 'none',
        display: 'flex',
        alignItems: 'center',
        gap: 4,
      }}
    >
      <Handle type="source" position={Position.Top} id="top" style={handleStyle()} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={handleStyle()} />
      <Handle type="source" position={Position.Left} id="left" style={handleStyle()} />
      <Handle type="source" position={Position.Right} id="right" style={handleStyle()} />
      <span style={{ fontSize: 10 }}>{'\u25B6'}</span>
      Start
    </div>
  );
}

export const StartNode = memo(StartNodeComponent);

type JudgmentNodeProps = NodeProps & { data: AgentNodeData };

function JudgmentNodeComponent({ data, selected }: JudgmentNodeProps) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: 'relative',
        width: 90,
        height: 90,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'grab',
      }}
    >
      {/* Diamond */}
      <div
        style={{
          position: 'absolute',
          width: 65,
          height: 65,
          background: `${data.color}08`,
          border: `2px solid ${data.color}`,
          borderRadius: 8,
          transform: 'rotate(45deg)',
          boxShadow: selected
            ? `0 0 0 2px ${data.color}40, 0 4px 12px rgba(0,0,0,0.12)`
            : hovered
              ? '0 4px 12px rgba(0,0,0,0.12)'
              : '0 1px 3px rgba(0,0,0,0.08)',
          transition: 'box-shadow 0.2s ease',
        }}
      />
      {/* Label */}
      <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', pointerEvents: 'none' }}>
        <div style={{ fontSize: 12, marginBottom: 1 }}>{'\u2753'}</div>
        <div style={{ fontSize: 9, fontWeight: 600, maxWidth: 55, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {agentRegistry[data.agent]?.name ?? data.agent}
        </div>
      </div>
      <Handle type="source" position={Position.Top} id="top" style={handleStyle()} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={handleStyle()} />
      <Handle type="source" position={Position.Left} id="left" style={handleStyle()} />
      <Handle type="source" position={Position.Right} id="right" style={handleStyle()} />
      <Handle type="target" position={Position.Top} id="target-top" style={handleStyle()} />
      <Handle type="target" position={Position.Bottom} id="target-bottom" style={handleStyle()} />
      <Handle type="target" position={Position.Left} id="target-left" style={handleStyle()} />
      <Handle type="target" position={Position.Right} id="target-right" style={handleStyle()} />
    </div>
  );
}

export const JudgmentNode = memo(JudgmentNodeComponent);
