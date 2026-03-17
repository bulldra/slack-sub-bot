import express, { type Request, type Response } from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';
import { agentRegistry } from '../src/utils/agentRegistry.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FLOWS_DIR = path.resolve(__dirname, '../../../src/conf/flows');

const app = express();
app.use(cors());
app.use(express.json());

interface FlowStep {
  agent: string;
  arguments: Record<string, unknown>;
}

interface FlowDefinition {
  name: string;
  description: string;
  command: string;
  steps: FlowStep[];
}

// GET /api/flows -- フロー一覧
app.get('/api/flows', (_req: Request, res: Response) => {
  try {
    if (!fs.existsSync(FLOWS_DIR)) {
      res.json([]);
      return;
    }

    const files = fs.readdirSync(FLOWS_DIR).filter(f => f.endsWith('.yaml'));
    const flows = files.map(file => {
      const content = fs.readFileSync(path.join(FLOWS_DIR, file), 'utf-8');
      const flow = yaml.load(content) as FlowDefinition;
      return {
        name: flow.name,
        command: flow.command,
        description: flow.description,
        stepCount: flow.steps ? flow.steps.length : 0,
      };
    });

    res.json(flows);
  } catch (err) {
    console.error('Failed to list flows:', err);
    res.status(500).json({ error: 'Failed to list flows' });
  }
});

// GET /api/flows/:name -- 単一フロー取得
app.get('/api/flows/:name', (req: Request, res: Response) => {
  try {
    const filePath = path.join(FLOWS_DIR, `${req.params.name}.yaml`);

    if (!filePath.startsWith(FLOWS_DIR)) {
      res.status(400).json({ error: 'Invalid flow name' });
      return;
    }

    if (!fs.existsSync(filePath)) {
      res.status(404).json({ error: 'Flow not found' });
      return;
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const flow = yaml.load(content) as FlowDefinition;
    res.json(flow);
  } catch (err) {
    console.error('Failed to read flow:', err);
    res.status(500).json({ error: 'Failed to read flow' });
  }
});

// PUT /api/flows/:name -- フロー保存
app.put('/api/flows/:name', (req: Request, res: Response) => {
  try {
    const filePath = path.join(FLOWS_DIR, `${req.params.name}.yaml`);

    if (!filePath.startsWith(FLOWS_DIR)) {
      res.status(400).json({ error: 'Invalid flow name' });
      return;
    }

    if (!fs.existsSync(FLOWS_DIR)) {
      fs.mkdirSync(FLOWS_DIR, { recursive: true });
    }

    const flow = req.body as FlowDefinition;

    if (!flow.name || !flow.command || !flow.steps) {
      res.status(400).json({ error: 'Missing required fields: name, command, steps' });
      return;
    }

    const yamlContent = yaml.dump(flow, {
      lineWidth: -1,
      noRefs: true,
      quotingType: '"',
      forceQuotes: false,
    });

    fs.writeFileSync(filePath, yamlContent, 'utf-8');
    res.json({ success: true, name: flow.name });
  } catch (err) {
    console.error('Failed to save flow:', err);
    res.status(500).json({ error: 'Failed to save flow' });
  }
});

// DELETE /api/flows/:name -- フロー削除
app.delete('/api/flows/:name', (req: Request, res: Response) => {
  try {
    const filePath = path.join(FLOWS_DIR, `${req.params.name}.yaml`);

    if (!filePath.startsWith(FLOWS_DIR)) {
      res.status(400).json({ error: 'Invalid flow name' });
      return;
    }

    if (!fs.existsSync(filePath)) {
      res.status(404).json({ error: 'Flow not found' });
      return;
    }

    fs.unlinkSync(filePath);
    res.json({ success: true });
  } catch (err) {
    console.error('Failed to delete flow:', err);
    res.status(500).json({ error: 'Failed to delete flow' });
  }
});

// GET /api/agents -- エージェントメタデータ一覧
app.get('/api/agents', (_req: Request, res: Response) => {
  res.json(agentRegistry);
});

app.listen(3001, () => {
  console.log('API server running on http://localhost:3001');
});
