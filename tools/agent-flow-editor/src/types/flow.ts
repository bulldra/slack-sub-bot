export interface FlowStep {
  agent: string;
  arguments: Record<string, unknown>;
}

export interface FlowDefinition {
  name: string;
  description: string;
  command: string;
  steps: FlowStep[];
}

export interface FlowListItem {
  name: string;
  command: string;
  description: string;
  stepCount: number;
}
