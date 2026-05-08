import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { initDatabase } from './database/init.js';
import { getDashboardData } from './services/jobRepository.js';
import { latestLogs } from './services/logRepository.js';
import { logEvents, logger } from './utils/logger.js';
import { config } from './utils/config.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'dashboard', 'public')));

app.get('/api/dashboard', async (req, res) => {
  try {
    const data = await getDashboardData({
      search: req.query.search || '',
      page: req.query.page || 1,
      limit: req.query.limit || 20
    });
    res.json(data);
  } catch (error) {
    logger.error('Dashboard data failed', { error: error.message });
    res.status(500).json({ error: 'dashboard_data_failed' });
  }
});

app.get('/api/logs', async (_req, res) => {
  try {
    res.json(await latestLogs(100));
  } catch (error) {
    logger.error('Logs query failed', { error: error.message });
    res.status(500).json({ error: 'logs_query_failed' });
  }
});

app.get('/api/status', (_req, res) => {
  res.json({
    status: 'online',
    intervalMs: config.bot.intervalMs,
    keywords: config.bot.searchKeywords,
    minMatchScore: config.bot.minMatchScore
  });
});

app.get('/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders?.();

  const send = (entry) => res.write(`data: ${JSON.stringify(entry)}\n\n`);
  logEvents.on('log', send);
  req.on('close', () => logEvents.off('log', send));
});

app.get('*', (_req, res) => {
  res.sendFile(path.join(__dirname, 'dashboard', 'public', 'index.html'));
});

await initDatabase();

app.listen(config.app.port, () => {
  logger.info(`Dashboard running at http://localhost:${config.app.port}`);
});
