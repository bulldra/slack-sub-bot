import { useState } from 'react';

interface FlowToolbarProps {
  flowName: string;
  flowDescription: string;
  flowCommand: string;
  onFlowNameChange: (name: string) => void;
  onFlowDescriptionChange: (desc: string) => void;
  onFlowCommandChange: (cmd: string) => void;
  onSave: () => void;
  onDelete: () => void;
  saving: boolean;
  hasUnsavedChanges: boolean;
}

const inputBaseStyle: React.CSSProperties = {
  padding: '7px 12px',
  border: '1px solid #e2e8f0',
  borderRadius: 8,
  fontSize: 13,
  background: '#fff',
  outline: 'none',
  transition: 'border-color 0.15s, box-shadow 0.15s',
};

export function FlowToolbar({
  flowName,
  flowDescription,
  flowCommand,
  onFlowNameChange,
  onFlowDescriptionChange,
  onFlowCommandChange,
  onSave,
  onDelete,
  saving,
  hasUnsavedChanges,
}: FlowToolbarProps) {
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const handleDelete = () => {
    if (!flowName) return;
    if (window.confirm(`"${flowName}" を削除しますか?`)) {
      onDelete();
    }
  };

  const getInputStyle = (field: string, extra?: React.CSSProperties): React.CSSProperties => ({
    ...inputBaseStyle,
    ...extra,
    borderColor: focusedField === field ? '#3b82f6' : '#e2e8f0',
    boxShadow: focusedField === field ? '0 0 0 3px rgba(59,130,246,0.12)' : 'none',
  });

  return (
    <div
      style={{
        height: 56,
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: 12,
        background: 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        flexShrink: 0,
      }}
    >
      <input
        value={flowName}
        onChange={e => onFlowNameChange(e.target.value)}
        onFocus={() => setFocusedField('name')}
        onBlur={() => setFocusedField(null)}
        placeholder="Flow name"
        style={getInputStyle('name', { width: 130, fontWeight: 500 })}
      />
      <input
        value={flowCommand}
        onChange={e => onFlowCommandChange(e.target.value)}
        onFocus={() => setFocusedField('command')}
        onBlur={() => setFocusedField(null)}
        placeholder="/command"
        style={getInputStyle('command', { width: 130, fontFamily: '"SF Mono", "Fira Code", monospace', fontSize: 12 })}
      />
      <input
        value={flowDescription}
        onChange={e => onFlowDescriptionChange(e.target.value)}
        onFocus={() => setFocusedField('desc')}
        onBlur={() => setFocusedField(null)}
        placeholder="Description"
        style={getInputStyle('desc', { flex: 1 })}
      />

      {/* Save status indicator */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: hasUnsavedChanges ? '#f59e0b' : '#22c55e',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{ fontSize: 8 }}>{hasUnsavedChanges ? '\u{1F7E0}' : '\u{1F7E2}'}</span>
        {hasUnsavedChanges ? 'Unsaved' : 'Saved'}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={onSave}
          disabled={saving || !flowName}
          onMouseEnter={e => { if (!saving && flowName) e.currentTarget.style.background = '#2563eb'; }}
          onMouseLeave={e => { e.currentTarget.style.background = hasUnsavedChanges ? '#3b82f6' : '#93c5fd'; }}
          style={{
            padding: '7px 18px',
            fontSize: 13,
            fontWeight: 600,
            border: 'none',
            borderRadius: 8,
            background: hasUnsavedChanges ? '#3b82f6' : '#93c5fd',
            color: '#fff',
            cursor: saving || !flowName ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.7 : 1,
            transition: 'background 0.15s, opacity 0.15s',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {saving ? '\u23F3' : '\u{1F4BE}'} {saving ? 'Saving...' : 'Save'}
        </button>
        <button
          onClick={handleDelete}
          disabled={!flowName}
          onMouseEnter={e => { if (flowName) { e.currentTarget.style.background = '#fef2f2'; e.currentTarget.style.borderColor = '#ef4444'; } }}
          onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = '#fca5a5'; }}
          style={{
            padding: '7px 18px',
            fontSize: 13,
            fontWeight: 600,
            border: '1px solid #fca5a5',
            borderRadius: 8,
            background: '#fff',
            color: '#ef4444',
            cursor: !flowName ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {'\u{1F5D1}'} Delete
        </button>
      </div>
    </div>
  );
}
