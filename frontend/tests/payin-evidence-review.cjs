/* Run against Local Vite only, with VITE_API_BASE_URL=http://127.0.0.1:5176.
 * All API responses are synthetic; all non-local requests are blocked.
 * NODE_PATH can point to the bundled Playwright runtime. No production access.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const origin = 'http://127.0.0.1:5176';
const out = process.env.PAYIN_UI_EVIDENCE_DIR || path.join(os.tmpdir(), 'moobaan-integrity-ui');
fs.mkdirSync(out, { recursive: true });
const bank = { id: '11111111-1111-1111-1111-111111111111', credit: 600,
  effective_at: '2026-03-02T03:48:00Z', channel: 'K PLUS', description: 'SYNTHETIC TEST TRANSFER' };
const base = { id: 1, house_number: 'TEST/67', house_id: 1, amount: 600,
  transfer_date: bank.effective_at, transfer_hour: 10, transfer_minute: 48,
  slip_image_url: 'test.png', status: 'PENDING', is_matched: true,
  matched_statement_txn_id: bank.id, posting_status: 'MATCHED', matched_statement: bank, evidence_revision: 'local-review-token' };
const tests = [];
async function run() {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    for (const scenario of ['desktop', 'mobile', 'drift', 'timeDrift', 'missingBank', 'missingSlip', 'imageFailure', 'loadFailure', 'serverConflict', 'match', 'tokyo']) {
      const context = await browser.newContext({ viewport: { width: scenario === 'mobile' ? 390 : 1280, height: 900 },
        timezoneId: scenario === 'tokyo' ? 'Asia/Tokyo' : 'America/New_York' });
      await context.addCookies([{ name: 'csrf_token', value: 'local-test', url: origin }]);
      const page = await context.newPage();
      const errors = [], remote = [], mutations = [];
      page.on('pageerror', err => errors.push(err.message));
      let detail = structuredClone(base);
      if (scenario === 'drift') detail.amount = 999;
      if (scenario === 'timeDrift') detail.transfer_date = '2026-03-02T06:41:00Z';
      if (scenario === 'missingBank') detail.matched_statement = null;
      if (scenario === 'missingSlip') detail.slip_image_url = null;
      if (scenario === 'match') { detail.is_matched = false; detail.matched_statement_txn_id = null; detail.matched_statement = null; }
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (!['127.0.0.1', 'localhost'].includes(url.hostname)) {
          remote.push(url.hostname); return route.abort();
        }
        if (!url.pathname.startsWith('/api/')) return route.continue();
        const json = (body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
        if (url.pathname === '/api/auth/me') return json({ id: 1, role: 'super_admin', full_name: 'Local test', is_active: true });
        if (url.pathname === '/api/notifications/count') return json({ unread_count: 0 });
        if (url.pathname === '/api/payin-reports') return json([scenario === 'match' ? detail : base]);
        if (url.pathname === '/api/payin-reports/1') return scenario === 'loadFailure' ? json({ detail: 'local failure' }, 500) : json(detail);
        if (url.pathname.endsWith('/slip')) {
          if (scenario === 'imageFailure') return route.fulfill({ status: 404, body: '' });
          return route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430"><rect width="350" height="430" fill="#e2e8f0"/><text x="25" y="80" font-size="20">SYNTHETIC TEST SLIP</text><text x="25" y="140" font-size="24">600 THB / 10:48</text><text x="25" y="200" font-size="18">NOT PAYMENT EVIDENCE</text></svg>' });
        }
        if (url.pathname.includes('candidates')) return json({ candidates: [{ ...bank, is_perfect_match: true, time_diff_seconds: 0, amount_diff: 0 }], already_matched: [] });
        if (route.request().method() === 'POST') {
          assert.equal(route.request().postDataJSON().evidence_revision, 'local-review-token');
          mutations.push(url.pathname);
          if (scenario === 'serverConflict') return json({ detail: { code: 'EVIDENCE_CHANGED', message: 'LOCAL EVIDENCE CHANGED' } }, 400);
          return json({ status: 'posted', success: true, allocations: [] });
        }
        throw new Error('Unexpected local API: ' + url.pathname);
      });
      await page.goto(origin + '/admin/payins');
      if (scenario === 'match') {
        await page.getByRole('button', { name: 'จับคู่', exact: true }).click();
        await page.getByRole('button', { name: 'ตรวจหลักฐาน', exact: true }).click();
      } else await page.getByRole('button', { name: 'ยืนยันและบันทึก', exact: true }).click();
      const dialog = page.getByRole('dialog');
      await dialog.waitFor();
      const confirm = dialog.getByRole('button', { name: scenario === 'match' ? 'ตรวจหลักฐานแล้ว ยืนยันจับคู่' : 'ยืนยันและบันทึก', exact: true });
      if (scenario !== 'loadFailure') await dialog.getByRole('heading', { name: 'ข้อมูลที่กรอก' }).waitFor();
      if (['drift', 'timeDrift', 'missingBank', 'loadFailure', 'imageFailure'].includes(scenario)) {
        if (scenario === 'imageFailure') await dialog.getByText('โหลดรูปสลิปไม่สำเร็จ กรุณาปิดและเปิดตรวจใหม่').waitFor();
        if (scenario === 'loadFailure') await dialog.getByRole('alert').waitFor();
        assert.equal(await confirm.isDisabled(), true, scenario);
        assert.equal(mutations.length, 0);
      } else {
        assert.equal(await confirm.isEnabled(), true, scenario);
        if (scenario !== 'missingSlip') await dialog.locator('img').waitFor();
        if (['desktop', 'mobile', 'tokyo'].includes(scenario)) {
          assert.match(await dialog.innerText(), /10:48/);
          const box = await dialog.boundingBox();
          assert(box.x >= 0 && box.x + box.width <= page.viewportSize().width + 1);
          assert.equal(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth + 1), true);
          await page.screenshot({ path: path.join(out, scenario + '.png'), fullPage: true });
        }
        await confirm.click();
        if (scenario === 'serverConflict') {
          await dialog.getByRole('alert').filter({ hasText: 'LOCAL EVIDENCE CHANGED' }).waitFor();
          assert.equal(await dialog.isVisible(), true);
        } else await dialog.waitFor({ state: 'detached' });
        assert.equal(mutations.length, 1);
        assert.equal(mutations[0].endsWith(scenario === 'match' ? '/match' : '/confirm-and-post'), true);
      }
      assert.deepEqual(errors, [], scenario);
      assert.deepEqual(remote, [], 'No remote requests permitted');
      tests.push({ scenario, passed: true, mutations: mutations.length });
      await context.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ local_only: true, synthetic_api: true, tests }, null, 2));
  console.log(JSON.stringify({ passed: tests.length, evidence: out }));
}
run().catch(err => { console.error(err); process.exit(1); });
