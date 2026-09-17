// Pass the installed Playwright module path as the first argument.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
require('node:fs').mkdirSync('reports', { recursive: true });

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:5173');
    await page.locator('input[type=file]').setInputFiles(path.resolve('tests/fixtures/rounded-controls.png'));
    await page.getByRole('button', { name: 'Reconstruct →', exact: true }).click();
    await page.getByLabel('Selected element').waitFor();
    await page.getByRole('button', { name: 'Select button Sign in', exact: true }).click();
    await page.getByLabel('Element text', { exact: true }).fill('Continue securely');
    await page.getByLabel('Font size', { exact: true }).fill('24');
    await page.getByLabel('Corner radius', { exact: true }).fill('10');
    await page.getByLabel('X position', { exact: true }).fill('245');
    await page.getByLabel('Fill color', { exact: true }).fill('#336644');
    await page.getByLabel('Text color', { exact: true }).fill('#ffffff');
    await page.getByRole('status').filter({ hasText: 'Preview and exports up to date' }).waitFor();
    const button = page.frameLocator('iframe').getByRole('button', { name: 'Continue securely', exact: true });
    await button.waitFor();
    const styles = await button.evaluate(e => { const s = getComputedStyle(e); return [s.fontSize, s.borderRadius, s.left, s.backgroundColor]; });
    assert.deepEqual(styles, ['24px', '10px', '245px', 'rgb(51, 102, 68)']);
    for (const [label, file] of [['↓ HTML / CSS', 'edited-html.zip'], ['↓ React project', 'edited-react.zip']]) {
      const event = page.waitForEvent('download');
      await page.getByRole('button', { name: label, exact: true }).click();
      await (await event).saveAs(path.resolve('reports', file));
    }
    await page.screenshot({ path: 'reports/editor-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: 'reports/editor-mobile.png', fullPage: true });
    // Failed updates must not expose an old export as though the edit succeeded.
    await page.route('**/render', route => route.fulfill({ status: 503, body: '{}' }));
    await page.getByLabel('Element text', { exact: true }).fill('Unsaved edit');
    await page.getByRole('button', { name: 'Retry edits' }).waitFor();
    assert.equal(await page.getByRole('button', { name: '↓ React project' }).isDisabled(), true);
    await page.unroute('**/render');
    await page.getByRole('button', { name: 'Retry edits' }).click();
    await page.getByRole('status').filter({ hasText: 'Preview and exports up to date' }).waitFor();
    await page.frameLocator('iframe').getByRole('button', { name: 'Unsaved edit', exact: true }).waitFor();
    assert.deepEqual(errors, []);
    console.log('PASS: click selection, edits, live preview, both downloads, mobile, failure gating, retry, no browser errors');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
