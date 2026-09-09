// Execute the actual page code with local state/IO stubs; no production connection.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { transformSync } = require('esbuild');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

const cash = fs.readFileSync('src/pages/admin/CashFlowReport.jsx', 'utf8');
const defaults = cash.match(/useEffect\(\(\) => \{([\s\S]*?)\}, \[\]\);/)[1];
for (const tz of ['UTC', 'America/New_York', 'Asia/Tokyo']) {
  process.env.TZ = tz;
  class Clock extends Date { constructor() { super('2026-12-31T17:30:00Z'); } }
  const actual = {};
  vm.runInNewContext(defaults, { Intl, Date: Clock, setFromDate: v => actual.start=v, setToDate: v => actual.end=v });
  assert.deepEqual(actual, { start: '2027-01-01', end: '2027-01-01' });
}

const history = fs.readFileSync('src/pages/resident/mobile/PaymentHistory.jsx', 'utf8');
const filtering = history.match(/const filteredPayins = ([\s\S]*?\n  \}\));/)[1];
const statuses = ['PENDING', 'SUBMITTED', 'ACCEPTED', 'DRAFT', 'REJECTED_NEEDS_FIX'];
const selected = vm.runInNewContext(filtering, { payinFilter: 'pending', payins: statuses.map(status => ({status})) });
assert.deepEqual(Array.from(selected, p => p.status), ['PENDING', 'SUBMITTED']);

const code = transformSync(fs.readFileSync('src/pages/resident/mobile/MobileDashboard.jsx','utf8'),
  { loader:'jsx', format:'cjs', jsx:'automatic' }).code;
function render(pending, balance) {
  const values = [[], { current_balance: balance, pending_payins: pending }, false, !!pending, null];
  let n=0;
  const module = { exports:{} };
  const wrapper = ({children}) => React.createElement('div', null, children);
  const stubRequire = name => {
    if (name === 'react') return {...React, useState: () => [values[n++], () => {}], useEffect: () => {}};
    if (name === 'react/jsx-runtime') return require(name);
    if (name === 'react-router-dom') return {Link: wrapper};
    if (name.endsWith('RoleContext')) return {useRole: () => ({currentHouseId:96})};
    if (name.endsWith('useLocale')) return {t: key => key};
    if (name.endsWith('api/client')) return {};
    if (name === 'lucide-react' || name.endsWith('Skeleton')) return new Proxy({}, {get: () => () => null});
    return wrapper;
  };
  vm.runInNewContext(code, {module, exports: module.exports, require:stubRequire, console});
  return renderToStaticMarkup(React.createElement(module.exports.default));
}
const pending = render(2, -600);
assert.ok(pending.includes('mobileDashboard.pendingReview'));
assert.ok(pending.includes('mobileDashboard.pendingExcluded'));
assert.ok(pending.includes('mobileDashboard.pendingEvidence: 2'));
assert.ok(pending.includes('฿600')); // Pending slips never change displayed confirmed balance.
assert.ok(!pending.includes('mobileDashboard.mustPay'));
assert.ok(!render(0,-600).includes('mobileDashboard.pendingExcluded'));
assert.ok(render(1,0).includes('mobileDashboard.pendingExcluded')); // Evidence remains visible even without debt.
console.log('R2 display passed: Bangkok dates in 3 timezones, pending statuses, resident rendered balance/message.');
