import fs from 'fs/promises';
import path from 'path';
import { rootPool } from './connection.js';
import { logger } from '../utils/logger.js';

export const initDatabase = async () => {
  const schemaPath = path.resolve('database', 'schema.sql');
  const sql = await fs.readFile(schemaPath, 'utf8');
  const statements = sql
    .split(';')
    .map((statement) => statement.trim())
    .filter(Boolean);

  for (const statement of statements) {
    await rootPool.query(statement);
  }

  logger.info('MySQL schema initialized');
};

if (process.argv[1]?.endsWith('database\\init.js') || process.argv[1]?.endsWith('database/init.js')) {
  initDatabase()
    .then(() => process.exit(0))
    .catch((error) => {
      logger.error('Database initialization failed', { error: error.message });
      process.exit(1);
    });
}
