import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';

const logDir = path.resolve('logs');
const logFile = path.join(logDir, 'bot.log');

if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

export const logEvents = new EventEmitter();

const write = (level, message, meta = {}) => {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    meta
  };
  const line = JSON.stringify(entry);
  fs.appendFileSync(logFile, `${line}\n`, 'utf8');
  logEvents.emit('log', entry);
  console[level === 'error' ? 'error' : 'log'](`[${entry.timestamp}] ${level.toUpperCase()} ${message}`);
};

export const logger = {
  info: (message, meta) => write('info', message, meta),
  warn: (message, meta) => write('warn', message, meta),
  error: (message, meta) => write('error', message, meta)
};
