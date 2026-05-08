import dotenv from 'dotenv';

dotenv.config({ path: '../.env' });
dotenv.config();

const splitList = (value) => (value || '')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);

const toBool = (value) => String(value).toLowerCase() === 'true';

export const config = {
  app: {
    port: Number(process.env.APP_PORT || 3000),
    env: process.env.NODE_ENV || 'development'
  },
  database: {
    host: process.env.DB_HOST || process.env.hotst || process.env.HOST || 'localhost',
    port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || process.env.sql_user || process.env.SQL_USER || 'root',
    password: process.env.DB_PASSWORD || process.env.Sql_password || process.env.SQL_PASSWORD || '',
    database: process.env.DB_NAME || 'job_bot'
  },
  bot: {
    targetUrl: process.env.MAGNETO_TARGET_URL || 'https://www.magneto365.com/co/trabajos/buscar',
    intervalMs: Number(process.env.SEARCH_INTERVAL_MS || 300000),
    maxPagesPerSearch: Number(process.env.MAX_PAGES_PER_SEARCH || 5),
    maxApplicationsPerCycle: Number(process.env.MAX_APPLICATIONS_PER_CYCLE || 20),
    minMatchScore: Number(process.env.MIN_MATCH_SCORE || 70),
    searchKeywords: splitList(process.env.SEARCH_KEYWORDS),
    targetLocations: splitList(process.env.TARGET_LOCATIONS),
    prioritySkills: splitList(process.env.PRIORITY_SKILLS),
    cvPath: process.env.CV_PATH || ''
  },
  browser: {
    channel: process.env.BROWSER_CHANNEL || 'msedge',
    userDataDir: process.env.USER_DATA_DIR,
    profileDirectory: process.env.PROFILE_DIRECTORY || 'Default',
    headless: toBool(process.env.HEADLESS),
    slowMo: Number(process.env.SLOW_MO_MS || 0)
  }
};
