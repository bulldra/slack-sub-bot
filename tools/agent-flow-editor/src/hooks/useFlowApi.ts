import { useState, useCallback } from 'react';
import type { FlowDefinition, FlowListItem } from '../types/flow';
import type { AgentMeta } from '../utils/agentRegistry';

export function useFlowApi() {
  const [flowList, setFlowList] = useState<FlowListItem[]>([]);
  const [agents, setAgents] = useState<Record<string, AgentMeta>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFlowList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/flows');
      if (!res.ok) throw new Error('Failed to fetch flow list');
      const data = await res.json();
      setFlowList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFlow = useCallback(async (name: string): Promise<FlowDefinition | null> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/flows/${encodeURIComponent(name)}`);
      if (!res.ok) throw new Error('Failed to fetch flow');
      return await res.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const saveFlow = useCallback(async (name: string, flow: FlowDefinition): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/flows/${encodeURIComponent(name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(flow),
      });
      if (!res.ok) throw new Error('Failed to save flow');
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteFlow = useCallback(async (name: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/flows/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete flow');
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch('/api/agents');
      if (!res.ok) throw new Error('Failed to fetch agents');
      const data = await res.json();
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, []);

  return {
    flowList,
    agents,
    loading,
    error,
    fetchFlowList,
    fetchFlow,
    saveFlow,
    deleteFlow,
    fetchAgents,
  };
}
