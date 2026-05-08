import { config } from '../utils/config.js';

const normalize = (value = '') => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase();

const salaryValue = (salary = '') => {
  const numbers = salary.match(/\d[\d.,]*/g) || [];
  return Math.max(...numbers.map((item) => Number(item.replace(/[.,]/g, ''))), 0);
};

const matchesSkill = (skill, text) => {
  const normalizedSkill = normalize(skill).trim();
  const explicitPatterns = {
    ia: /\b(?:ia|ai)\b|inteligencia artificial/,
    api: /\bapi(?:s)?\b|\brest\b/,
    apis: /\bapi(?:s)?\b|\brest\b/,
    'node.js': /\bnode(?:\.js|js)?\b/,
    nodejs: /\bnode(?:\.js|js)?\b/,
    'next.js': /\bnext(?:\.js|js)?\b/,
    fullstack: /\bfull\s*stack\b|\bfullstack\b/,
    'full stack': /\bfull\s*stack\b|\bfullstack\b/,
    '.net': /(?:^|[^a-z0-9])(?:\.net|net core|asp\.net)(?:[^a-z0-9]|$)/,
    'c#': /(?:^|[^a-z0-9])(?:c#|c sharp)(?:[^a-z0-9]|$)/,
    sql: /\bsql\b|sql server|\bmysql\b|\bpostgres(?:ql)?\b|\boracle\b/
  };

  if (explicitPatterns[normalizedSkill]) {
    return explicitPatterns[normalizedSkill].test(text);
  }

  const escaped = normalizedSkill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g, '\\s+');
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`).test(text);
};

export const analyzeJob = (job) => {
  const text = normalize([
    job.title,
    job.companyName,
    job.salary,
    job.location,
    job.modality,
    job.description
  ].join(' '));

  const matchedSkills = config.bot.prioritySkills.filter((skill) => matchesSkill(skill, text));
  let score = 25;

  score += Math.min(matchedSkills.length * 8, 40);

  if (config.bot.targetLocations.some((location) => text.includes(normalize(location)))) {
    score += 10;
  }

  if (/(remoto|remote|hibrido|hybrid)/.test(text)) {
    score += 10;
  }

  if (/(full stack|frontend|backend|react|node|software engineer|typescript|javascript)/.test(text)) {
    score += 10;
  }

  if (salaryValue(job.salary) >= 8000000) {
    score += 15;
  }

  score = Math.min(score, 100);

  const priority = score >= config.bot.minMatchScore && (
    /(senior|semi senior|semisenior|remoto|remote|hibrido|hybrid)/.test(text) || salaryValue(job.salary) >= 8000000
  ) ? 'alta' : score >= config.bot.minMatchScore ? 'normal' : 'baja';

  const recommendation = score >= config.bot.minMatchScore
    ? 'Postular'
    : 'Descartar por baja coincidencia';

  return {
    score,
    priority,
    recommendation,
    matchedSkills
  };
};
