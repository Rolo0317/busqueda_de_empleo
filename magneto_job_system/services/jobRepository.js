import { pool } from '../database/connection.js';

export const upsertCompany = async (name) => {
  const companyName = name || 'Confidencial';
  await pool.execute(
    'INSERT INTO companies (name) VALUES (?) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP',
    [companyName]
  );
  const [rows] = await pool.execute('SELECT id FROM companies WHERE name = ?', [companyName]);
  return rows[0].id;
};

export const upsertJob = async (job, analysis) => {
  const companyId = await upsertCompany(job.companyName);
  await pool.execute(
    `INSERT INTO jobs
      (company_id, platform, title, company_name, salary, location, modality, published_at, url, description, match_score, priority, recommendation, status)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE
      company_id = VALUES(company_id),
      title = VALUES(title),
      company_name = VALUES(company_name),
      salary = VALUES(salary),
      location = VALUES(location),
      modality = VALUES(modality),
      published_at = VALUES(published_at),
      description = VALUES(description),
      match_score = VALUES(match_score),
      priority = VALUES(priority),
      recommendation = VALUES(recommendation),
      last_seen_at = CURRENT_TIMESTAMP`,
    [
      companyId,
      job.platform,
      job.title,
      job.companyName,
      job.salary,
      job.location,
      job.modality,
      job.publishedAt,
      job.url,
      job.description,
      analysis.score,
      analysis.priority,
      analysis.recommendation,
      analysis.score >= 70 ? 'found' : 'discarded'
    ]
  );
  const [rows] = await pool.execute('SELECT id FROM jobs WHERE url = ?', [job.url]);
  await syncSkills(rows[0].id, analysis.matchedSkills);
  return rows[0].id;
};

export const hasApplication = async (jobId) => {
  const [rows] = await pool.execute('SELECT id FROM applications WHERE job_id = ?', [jobId]);
  return rows.length > 0;
};

export const recordApplication = async (jobId, status, response = '') => {
  await pool.execute(
    `INSERT INTO applications (job_id, status, response)
     VALUES (?, ?, ?)
     ON DUPLICATE KEY UPDATE status = VALUES(status), response = VALUES(response), updated_at = CURRENT_TIMESTAMP`,
    [jobId, status, response]
  );
  await pool.execute('UPDATE jobs SET status = ? WHERE id = ?', [status === 'applied' ? 'applied' : status, jobId]);
};

export const createSearch = async (keyword) => {
  const [result] = await pool.execute('INSERT INTO searches (keyword) VALUES (?)', [keyword]);
  return result.insertId;
};

export const finishSearch = async (searchId, jobsFound, status = 'completed', errorMessage = null) => {
  await pool.execute(
    'UPDATE searches SET finished_at = CURRENT_TIMESTAMP, jobs_found = ?, status = ?, error_message = ? WHERE id = ?',
    [jobsFound, status, errorMessage, searchId]
  );
};

export const getDashboardData = async ({ search = '', page = 1, limit = 20 }) => {
  const safeLimit = Math.min(Math.max(Number(limit) || 20, 1), 100);
  const safePage = Math.max(Number(page) || 1, 1);
  const offset = (safePage - 1) * safeLimit;
  const like = `%${search}%`;
  const [jobs] = await pool.query(
    `SELECT * FROM jobs
     WHERE title LIKE ? OR company_name LIKE ? OR location LIKE ?
     ORDER BY last_seen_at DESC
     LIMIT ${safeLimit} OFFSET ${offset}`,
    [like, like, like]
  );
  const [statsRows] = await pool.query(`
    SELECT
      COUNT(*) AS total_jobs,
      SUM(status = 'applied') AS applied_jobs,
      AVG(match_score) AS avg_score,
      SUM(priority = 'alta') AS high_priority_count
    FROM jobs
  `);
  const [searches] = await pool.query('SELECT * FROM searches ORDER BY started_at DESC LIMIT 10');
  return { jobs, stats: statsRows[0], searches };
};

const syncSkills = async (jobId, skills) => {
  for (const skill of skills) {
    await pool.execute('INSERT INTO skills (name) VALUES (?) ON DUPLICATE KEY UPDATE name = VALUES(name)', [skill]);
    const [rows] = await pool.execute('SELECT id FROM skills WHERE name = ?', [skill]);
    await pool.execute(
      'INSERT IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)',
      [jobId, rows[0].id]
    );
  }
};
