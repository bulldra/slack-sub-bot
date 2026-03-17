import { useState, useEffect, useCallback } from 'react';
import type { Node } from '@xyflow/react';
import type { AgentNodeData } from '../utils/yamlConverter';
import { agentRegistry } from '../utils/agentRegistry';

interface ArgumentEditorProps {
  selectedNode: Node | null;
  onUpdateNodeData: (nodeId: string, args: Record<string, unknown>) => void;
}

export function ArgumentEditor({ selectedNode, onUpdateNodeData }: ArgumentEditorProps) {
  const [jsonText, setJsonText] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedNode) {
      const data = selectedNode.data as AgentNodeData;
      setJsonText(JSON.stringify(data.arguments || {}, null, 2));
      setParseError(null);
    }
  }, [selectedNode]);

  const handleChange = useCallback(
    (value: string) => {
      setJsonText(value);
      try {
        const parsed = JSON.parse(value);
        setParseError(null);
        if (selectedNode) {
          onUpdateNodeData(selectedNode.id, parsed);
        }
      } catch {
        setParseError('Invalid JSON');
      }
    },
    [selectedNode, onUpdateNodeData],
  );

  if (!selectedNode) return null;

  const data = selectedNode.data as AgentNodeData;
  const meta = agentRegistry[data.agent];

  return (
    <div
      style={{
        width: 300,
        borderLeft: '1px solid #e2e8f0',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header with node color */}
      <div
        style={{
          padding: '14px 16px',
          borderBottom: '1px solid #e2e8f0',
          borderLeft: `4px solid ${data.color}`,
          background: '#fafbfc',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: data.color,
              flexShrink: 0,
            }}
          />
          <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
            {meta?.name ?? data.agent}
          </h3>
        </div>
        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4, paddingLeft: 16 }}>
          Node Properties
        </div>
      </div>

      <div style={{ padding: '14px 16px', flex: 1, overflowY: 'auto' }}>
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Agent
          </label>
          <div
            style={{
              padding: '8px 12px',
              background: `${data.color}08`,
              border: `1px solid ${data.color}30`,
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 500,
              color: '#1e293b',
            }}
          >
            {data.agent}
          </div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Description
          </label>
          <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>{data.description}</div>
        </div>

        {/* Context I/O */}
        {meta && (meta.contextInputs.length > 0 || meta.contextOutputs.length > 0) && (
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Context I/O
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {meta.contextInputs.length > 0 && (
                <div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 3 }}>Inputs</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {meta.contextInputs.map((key) => (
                      <span
                        key={key}
                        style={{
                          fontSize: 11,
                          fontWeight: 500,
                          background: '#dbeafe',
                          color: '#1d4ed8',
                          padding: '2px 8px',
                          borderRadius: 4,
                        }}
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {meta.contextOutputs.length > 0 && (
                <div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 3 }}>Outputs</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {meta.contextOutputs.map((key) => (
                      <span
                        key={key}
                        style={{
                          fontSize: 11,
                          fontWeight: 500,
                          background: '#dcfce7',
                          color: '#15803d',
                          padding: '2px 8px',
                          borderRadius: 4,
                        }}
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Arguments (JSON)
          </label>
          <textarea
            value={jsonText}
            onChange={e => handleChange(e.target.value)}
            style={{
              width: '100%',
              minHeight: 140,
              fontFamily: '"SF Mono", "Fira Code", "Consolas", monospace',
              fontSize: 12,
              lineHeight: 1.6,
              padding: 12,
              border: parseError ? '1px solid #ef4444' : '1px solid #e2e8f0',
              borderRadius: 8,
              background: '#f1f5f9',
              resize: 'vertical',
              boxSizing: 'border-box',
              outline: 'none',
              color: '#1e293b',
              transition: 'border-color 0.15s, box-shadow 0.15s',
            }}
            onFocus={e => {
              if (!parseError) {
                e.currentTarget.style.borderColor = '#3b82f6';
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59,130,246,0.12)';
              }
            }}
            onBlur={e => {
              if (!parseError) {
                e.currentTarget.style.borderColor = '#e2e8f0';
                e.currentTarget.style.boxShadow = 'none';
              }
            }}
          />
          {parseError && (
            <div style={{ color: '#ef4444', fontSize: 11, marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
              {'\u26A0'} {parseError}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
