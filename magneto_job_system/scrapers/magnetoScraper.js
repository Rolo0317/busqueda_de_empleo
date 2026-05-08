import fs from 'fs';
import { config } from '../utils/config.js';
import { logger } from '../utils/logger.js';

const humanDelay = async (page, min = 400, max = 1200) => {
  await page.waitForTimeout(Math.floor(Math.random() * (max - min + 1)) + min);
};

const clean = (value = '') => value.replace(/\s+/g, ' ').trim();

export class MagnetoScraper {
  constructor(context) {
    this.context = context;
    this.page = null;
  }

  async init() {
    this.page = this.context.pages()[0] || await this.context.newPage();
    this.page.setDefaultTimeout(20000);
  }

  async ensureReady() {
    await this.page.goto(config.bot.targetUrl, { waitUntil: 'domcontentloaded' });
    await this.page.waitForLoadState('networkidle').catch(() => {});
    const loginVisible = await this.page.getByText(/iniciar sesion|iniciar sesión/i).count();
    if (loginVisible > 0) {
      logger.warn('Magneto no tiene sesion activa. Abre Chrome/Edge con este perfil e inicia sesion una vez.');
    }
  }

  async search(keyword) {
    logger.info(`Searching Magneto keyword: ${keyword}`);
    await this.page.goto(config.bot.targetUrl, { waitUntil: 'domcontentloaded' });
    await this.page.waitForLoadState('networkidle').catch(() => {});

    const searchInput = this.page.locator('input[name="search"]').first();
    await searchInput.waitFor({ state: 'visible' });
    await searchInput.fill('');
    await humanDelay(this.page);
    await searchInput.type(keyword, { delay: 40 });
    await searchInput.press('Enter');
    await this.waitForResults();

    const jobs = [];
    const seen = new Set();

    for (let pageNumber = 1; pageNumber <= config.bot.maxPagesPerSearch; pageNumber += 1) {
      const pageJobs = await this.extractVisibleJobs(keyword);
      for (const job of pageJobs) {
        if (!seen.has(job.url)) {
          seen.add(job.url);
          jobs.push(job);
        }
      }

      const moved = await this.goToNextPage();
      if (!moved) break;
      await this.waitForResults();
    }

    logger.info(`Magneto keyword finished: ${keyword}`, { jobsFound: jobs.length });
    return jobs;
  }

  async openDescription(job) {
    const detail = await this.context.newPage();
    try {
      await detail.goto(job.url, { waitUntil: 'domcontentloaded' });
      await detail.waitForLoadState('networkidle').catch(() => {});
      const bodyText = clean(await detail.locator('body').innerText().catch(() => ''));
      return { ...job, description: bodyText };
    } finally {
      await detail.close();
    }
  }

  async apply(job) {
    const detail = await this.context.newPage();
    try {
      await detail.goto(job.url, { waitUntil: 'domcontentloaded' });
      await detail.waitForLoadState('networkidle').catch(() => {});
      await this.attachCv(detail);

      const applyButton = detail
        .locator('a,button')
        .filter({ hasText: /aplicar|postular|postularme/i })
        .first();

      if (await applyButton.count() === 0) {
        return { status: 'no_available', response: 'No apply button found' };
      }

      await applyButton.click();
      await humanDelay(detail, 800, 1600);
      await this.attachCv(detail);

      if (await this.hasQuestionForm(detail)) {
        return {
          status: 'no_available',
          response: 'Application requires questions; use the Python bot question flow.'
        };
      }

      await this.clickOptionalFormButtons(detail);
      return { status: 'applied', response: 'Application flow triggered' };
    } catch (error) {
      return { status: 'error', response: error.message };
    } finally {
      await detail.close();
    }
  }

  async waitForResults() {
    await this.page.waitForLoadState('networkidle').catch(() => {});
    await this.page.waitForTimeout(1500);
  }

  async extractVisibleJobs(keyword) {
    const cards = this.page.locator([
      'div[class*="mg_job_card"]',
      'article',
      'li',
      'div:has(h2 a[href*="/empleos/"])'
    ].join(','));
    const count = await cards.count();
    const jobs = [];

    for (let index = 0; index < count; index += 1) {
      const card = cards.nth(index);
      const link = card.locator('h2 a[href], a[href*="/empleos/"]').first();
      if (await link.count() === 0) continue;

      const href = await link.getAttribute('href');
      if (!href) continue;

      const text = clean(await card.innerText().catch(() => ''));
      const lines = text.split(/\n|\|/).map(clean).filter(Boolean);
      const title = clean(await link.innerText().catch(() => lines[1] || keyword));
      const url = new URL(href, 'https://www.magneto365.com').toString();

      jobs.push({
        platform: 'Magneto365',
        title,
        companyName: this.extractCompany(lines),
        salary: this.extractSalary(lines),
        location: this.extractLocation(lines),
        modality: this.extractModality(lines),
        publishedAt: this.extractDate(lines),
        url,
        description: text
      });
    }

    return jobs;
  }

  async goToNextPage() {
    const nextButton = this.page
      .locator('a,button')
      .filter({ hasText: /siguiente|next|>/i })
      .last();

    if (await nextButton.count() === 0) return false;
    if (!(await nextButton.isEnabled().catch(() => false))) return false;

    await nextButton.click();
    await humanDelay(this.page);
    return true;
  }

  async attachCv(page) {
    if (!config.bot.cvPath || !fs.existsSync(config.bot.cvPath)) return;
    const inputs = page.locator('input[type="file"]');
    const count = await inputs.count();
    for (let index = 0; index < count; index += 1) {
      await inputs.nth(index).setInputFiles(config.bot.cvPath).catch(() => {});
    }
  }

  async hasQuestionForm(page) {
    const bodyText = clean(await page.locator('body').innerText().catch(() => ''));
    return /preguntas|responder|enviar respuestas|solo falta/i.test(bodyText);
  }

  async clickOptionalFormButtons(page) {
    const buttons = page
      .locator('button,a')
      .filter({ hasText: /continuar|siguiente|enviar|finalizar|postular|aplicar/i });
    const count = Math.min(await buttons.count(), 5);
    for (let index = 0; index < count; index += 1) {
      const button = buttons.nth(index);
      if (await button.isVisible().catch(() => false)) {
        await button.click().catch(() => {});
        await humanDelay(page, 500, 1000);
      }
    }
  }

  extractCompany(lines) {
    return lines[2] || lines[1] || 'Confidencial';
  }

  extractSalary(lines) {
    return lines.find((line) => /\$|salario|convenir/i.test(line)) || 'No especificado';
  }

  extractLocation(lines) {
    return lines.find((line) => /bogota|bogotá|medellin|medellín|colombia|remoto|remote/i.test(line)) || 'No especificada';
  }

  extractModality(lines) {
    return lines.find((line) => /remoto|remote|hibrido|híbrido|presencial|indefinido|obra|labor/i.test(line)) || 'No especificada';
  }

  extractDate(lines) {
    return lines.find((line) => /hace|ayer|hoy|\d{4}-\d{2}-\d{2}/i.test(line)) || 'No especificada';
  }
}
