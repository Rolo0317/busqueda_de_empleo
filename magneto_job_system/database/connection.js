import mysql from 'mysql2/promise';
import { config } from '../utils/config.js';

export const rootPool = mysql.createPool({
  host: config.database.host,
  port: config.database.port,
  user: config.database.user,
  password: config.database.password,
  waitForConnections: true,
  connectionLimit: 10
});

export const pool = mysql.createPool({
  host: config.database.host,
  port: config.database.port,
  user: config.database.user,
  password: config.database.password,
  database: config.database.database,
  waitForConnections: true,
  connectionLimit: 10
});
