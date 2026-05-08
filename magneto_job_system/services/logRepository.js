import { pool } from '../database/connection.js';

export const saveLog = async (level, message, meta = {}) => {
  await pool.execute(
    'INSERT INTO logs (level, message, meta) VALUES (?, ?, ?)',
    [level, message, JSON.stringify(meta)]
  );
};

export const latestLogs = async (limit = 100) => {
  const [rows] = await pool.execute(
    'SELECT * FROM logs ORDER BY created_at DESC LIMIT ?',
    [Number(limit)]
  );
  return rows.reverse();
};
