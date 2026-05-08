import { initDatabase } from '../database/init.js';
import { launchPersistentBrowser } from './browser.js';
import { MagnetoScraper } from '../scrapers/magnetoScraper.js';
import { analyzeJob } from '../services/scoringService.js';
import {
  createSearch,
  finishSearch,
  hasApplication,
  recordApplication,
  upsertJob
} from '../services/jobRepository.js';
import { saveLog } from '../services/logRepository.js';
import { config } from '../utils/config.js';
import { logger, logEvents } from '../utils/logger.js';

let isRunning = false;

logEvents.on('log', (entry) => {
  saveLog(entry.level, entry.message, entry.meta).catch(() => {});
});

export const runBotCycle = async (scraper) => {
  if (isRunning) {
    logger.warn('Previous cycle still running. Skipping this tick.');
    return;
  }

  isRunning = true;
  let applicationsThisCycle = 0;

  try {
    await scraper.ensureReady();

    for (const keyword of config.bot.searchKeywords) {
      const searchId = await createSearch(keyword);
      try {
        const jobs = await scraper.search(keyword);
        await finishSearch(searchId, jobs.length);

        for (const rawJob of jobs) {
          const detailedJob = await scraper.openDescription(rawJob);
          const analysis = analyzeJob(detailedJob);
          const jobId = await upsertJob(detailedJob, analysis);

          logger.info('Job analyzed', {
            title: detailedJob.title,
            score: analysis.score,
            priority: analysis.priority
          });

          if (analysis.score < config.bot.minMatchScore) continue;
          if (await hasApplication(jobId)) continue;
          if (applicationsThisCycle >= config.bot.maxApplicationsPerCycle) continue;

          const result = await scraper.apply(detailedJob);
          await recordApplication(jobId, result.status, result.response);
          applicationsThisCycle += result.status === 'applied' ? 1 : 0;
          logger.info('Application processed', {
            title: detailedJob.title,
            status: result.status,
            response: result.response
          });
        }
      } catch (error) {
        await finishSearch(searchId, 0, 'error', error.message);
        logger.error('Search failed', { keyword, error: error.message });
      }
    }
  } finally {
    isRunning = false;
  }
};

export const startBot = async () => {
  await initDatabase();
  const context = await launchPersistentBrowser();
  const scraper = new MagnetoScraper(context);
  await scraper.init();

  await runBotCycle(scraper);
  setInterval(() => {
    runBotCycle(scraper).catch((error) => logger.error('Bot cycle crashed', { error: error.message }));
  }, config.bot.intervalMs);

  logger.info('Autonomous bot started', { intervalMs: config.bot.intervalMs });
};

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}`) {
  startBot().catch((error) => {
    logger.error('Bot startup failed', { error: error.message });
    process.exit(1);
  });
}
