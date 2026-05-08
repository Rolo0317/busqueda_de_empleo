import { chromium } from 'playwright';
import { config } from '../utils/config.js';

export const launchPersistentBrowser = async () => {
  return chromium.launchPersistentContext(config.browser.userDataDir, {
    channel: config.browser.channel,
    headless: config.browser.headless,
    slowMo: config.browser.slowMo,
    viewport: { width: 1440, height: 920 },
    args: [
      `--profile-directory=${config.browser.profileDirectory}`,
      '--disable-blink-features=AutomationControlled',
      '--no-default-browser-check',
      '--no-first-run'
    ]
  });
};
