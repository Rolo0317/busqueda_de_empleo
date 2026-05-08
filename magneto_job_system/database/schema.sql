CREATE DATABASE IF NOT EXISTS job_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_bot;

CREATE TABLE IF NOT EXISTS companies (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  website VARCHAR(500) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_companies_name (name)
);

CREATE TABLE IF NOT EXISTS jobs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  company_id BIGINT UNSIGNED NULL,
  platform VARCHAR(80) NOT NULL DEFAULT 'Magneto365',
  title VARCHAR(255) NOT NULL,
  company_name VARCHAR(255) NOT NULL,
  salary VARCHAR(255) NULL,
  location VARCHAR(255) NULL,
  modality VARCHAR(120) NULL,
  published_at VARCHAR(120) NULL,
  url VARCHAR(1000) NOT NULL,
  description MEDIUMTEXT NULL,
  match_score INT NOT NULL DEFAULT 0,
  priority ENUM('baja','normal','alta') NOT NULL DEFAULT 'normal',
  recommendation VARCHAR(255) NULL,
  status ENUM('found','discarded','applied','error','no_available') NOT NULL DEFAULT 'found',
  first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_jobs_url (url(500)),
  INDEX idx_jobs_match_score (match_score),
  INDEX idx_jobs_priority (priority),
  INDEX idx_jobs_status (status),
  CONSTRAINT fk_jobs_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS applications (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  job_id BIGINT UNSIGNED NOT NULL,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status ENUM('applied','error','no_available','skipped') NOT NULL,
  response TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_applications_job (job_id),
  CONSTRAINT fk_applications_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS searches (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  keyword VARCHAR(255) NOT NULL,
  platform VARCHAR(80) NOT NULL DEFAULT 'Magneto365',
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  finished_at TIMESTAMP NULL,
  jobs_found INT NOT NULL DEFAULT 0,
  status ENUM('running','completed','error') NOT NULL DEFAULT 'running',
  error_message TEXT NULL,
  INDEX idx_searches_keyword (keyword),
  INDEX idx_searches_started_at (started_at)
);

CREATE TABLE IF NOT EXISTS skills (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_skills_name (name)
);

CREATE TABLE IF NOT EXISTS job_skills (
  job_id BIGINT UNSIGNED NOT NULL,
  skill_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (job_id, skill_id),
  CONSTRAINT fk_job_skills_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_job_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  level ENUM('info','warn','error') NOT NULL DEFAULT 'info',
  message TEXT NOT NULL,
  meta JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_logs_created_at (created_at),
  INDEX idx_logs_level (level)
);
