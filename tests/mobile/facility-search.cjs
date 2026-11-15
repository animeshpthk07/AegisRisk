const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const { _android } = require('playwright');

async function verifySession(session) {
  const [device] = await _android.devices();
  assert.ok(device, 'Android emulator must be connected');
  device.setDefaultTimeout(20000);
  try {
    const context = await device.launchBrowser({ hasTouch: true, viewport: null });
    const page = await context.newPage();
    await page.bringToFront();
    await page.goto('http://127.0.0.1:3000/#exposures');
    const panel = page.locator('#exposures');
    const search = panel.getByRole('textbox', { name: 'Search facilities' });
    const focusedSearch = search.and(page.locator(':focus'));
    const picker = panel.getByLabel('Inspect a facility', { exact: true });
    const status = panel.getByRole('status');
    const detail = panel.getByRole('heading', { name: 'Fictional Borrower 001 · SYN-001' });
    const count = n => status.filter({ hasText: 'Showing ' + n + ' of 40 facilities' }).waitFor();
    const userAgent = await page.evaluate(() => navigator.userAgent);
    assert.match(userAgent, /Android/);
    const viewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight }));
    assert.ok(viewport.width > 0 && viewport.width < 600, 'Expected a phone-sized CSS viewport');
    console.log(device.model(), userAgent, viewport);
    await count(40);
    // Let the initial anchor navigation settle before tapping the field.
    await search.evaluate(field => field.scrollIntoView({ block: 'center', behavior: 'instant' }));
    await search.evaluate(field => field.addEventListener('touchstart', event => {
      if (event.isTrusted && event.touches.length > 0) field.dataset.receivedTouch = 'yes';
    }, { once: true }));
    await search.tap();
    assert.equal(await search.getAttribute('data-received-touch'), 'yes');
    // Android may dispatch the compatibility click and focus after touchend.
    await focusedSearch.waitFor({ state: 'visible', timeout: 10000 });
    await page.keyboard.insertText('SYN-001');
    assert.equal(await search.inputValue(), 'SYN-001');
    await count(1);
    await picker.selectOption('SYN-001');
    await detail.waitFor();
    await fs.mkdir('mobile-evidence', { recursive: true });
    await page.screenshot({ path: `mobile-evidence/session-${session}-filtered.png` });
    for (const control of [search, picker]) {
      const bounds = await control.boundingBox();
      const width = await page.evaluate(() => document.documentElement.clientWidth);
      assert.ok(bounds && bounds.x >= -1 && bounds.x + bounds.width <= width + 1,
        'Control must fit horizontally in the Android viewport');
    }
    await search.tap();
    await focusedSearch.waitFor({ state: 'visible', timeout: 10000 });
    await search.fill('');
    await count(40);
    await detail.waitFor({ state: 'detached' });
    assert.ok(await search.evaluate(el => el === document.activeElement));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: `mobile-evidence/session-${session}-restored.png` });
    console.log('40 → 1 → 40. Opened SYN-001, restored search focus and checked horizontal fit.');
    await context.close();
  } finally {
    await device.close();
  }
}

async function run() {
  await verifySession(1);
  await verifySession(2);
}

run().catch(error => { console.error(error); process.exitCode = 1; });
