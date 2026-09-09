// Execute the production client and Houses download handler with isolated browser I/O.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

async function run() {
  for (const tz of ['UTC', 'America/New_York', 'Asia/Tokyo']) {
    process.env.TZ = tz;
    let busy = new Set(), calls = [], clicked = [], revoked = [], errors = [], fail = false;
    const contents = new Blob(['download test']);
    const client = {interceptors: {request: {use() {}}, response: {use() {}}},
      async get(url, options) {
        calls.push({url, options});
        if (fail) throw new Error('HTTP download failed');
        return {data: contents};
      }};
    const context = vm.createContext({
      axios: {create: () => client}, Blob, Intl, Number, Set,
      Date: class extends Date { constructor() { super('2026-05-31T18:30:00Z'); } },
      setDownloadingStatements: update => { busy = update(busy); },
      toast: {error: message => errors.push(message)}, t: key => key,
      console: {error() {}},
      document: {body: {appendChild() {}, removeChild() {}}, createElement() {
        return {style: {}, click() { clicked.push(this.download); }};
      }},
      window: {URL: {createObjectURL(blob) { assert.equal(blob, contents); return 'blob:test'; },
        revokeObjectURL(url) { revoked.push(url); }}},
    });
    let source = fs.readFileSync(path.join(__dirname, 'src/api/client.js'), 'utf8');
    source = source.replace("import axios from 'axios';", '')
      .replaceAll('import.meta.env', '({PROD:true})').replaceAll('export const ', 'const ')
      .replace('export default apiClient;', '');
    vm.runInContext(source, context);
    const page = fs.readFileSync(path.join(__dirname, 'src/pages/admin/Houses.jsx'), 'utf8');
    const start = page.indexOf('  const downloadStatement = async');
    const end = page.indexOf('  const getStatusLabel', start);
    assert.ok(start > 0 && end > start);
    vm.runInContext(page.slice(start, end) + '\nglobalThis.download = downloadStatement;', context);
    for (const format of ['pdf', 'xlsx']) {
      await context.download(95, format);
      const call = calls.at(-1);
      assert.equal(call.url, '/api/accounting/statement/house/95');
      assert.equal(call.options.params.year, 2026);
      assert.equal(call.options.params.month, 6); // Bangkok month, even on May31 in UTC.
      assert.equal(call.options.params.format, format);
      assert.equal(call.options.responseType, 'blob');
      assert.equal(clicked.at(-1), `statement_house95_2026_6.${format}`);
      assert.equal(busy.size, 0);
    }
    fail = true;
    await context.download(95, 'pdf');
    assert.equal(errors.length, 1);
    assert.equal(clicked.length, 2);
    assert.equal(revoked.length, 2);
    assert.equal(busy.size, 0);
  }
  console.log('Statement download: PDF/XLSX, URL, Bangkok month, Blob, cleanup/error passed in 3 timezones');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
