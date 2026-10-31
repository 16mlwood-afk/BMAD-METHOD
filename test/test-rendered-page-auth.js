/**
 * test-rendered-page-auth.js — the signed-in mode of tools/check-rendered-page.js (friction WF-20260928-085).
 *
 * A protected app renders its sign-in form to a stranger, and the checks then grade the form. These cases
 * pin the plan (a credential only from an environment variable, only to the page's own origin, only over
 * https or to localhost) against two local servers on different origins, and — where playwright is
 * installed — render a local app that shows a sign-in form unless signed in.
 *
 * Run: node test/test-rendered-page-auth.js   (part of `npm run test:rendered-page`)
 *      PLAYWRIGHT_DIR=<a project with playwright> node test/test-rendered-page-auth.js   (browser half too)
 */

'use strict';
const assert = require('node:assert');
const http = require('node:http');
const { authPlan, headersFor, loadPlaywright, snapshotFromUrl, PLAYWRIGHT_INSTALL } = require('../tools/check-rendered-page.js');

let pass = 0;
let skipped = 0;
const failures = [];
async function it(name, fn) {
  try {
    await fn();
    pass += 1;
  } catch (error) {
    failures.push(`${name}\n      ${error.message}`);
  }
}

const KEY = 'test-key-7f3a';

/** GET with the given headers; resolves to the status code. node:http, so no experimental fetch. */
function get(url, headers) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { headers }, (res) => {
      res.resume();
      res.on('end', () => resolve(res.statusCode));
    });
    req.on('error', reject);
  });
}
const ENV = { TEST_API_KEY: KEY };

const APP = `<!doctype html><html><body style="background:#fff"><main id="root"></main><script>
  const root = document.getElementById('root');
  const token = localStorage.getItem('app_token');
  const signIn = '<form><p>Sign in to continue</p><input type="password"></form>';
  if (!token) root.innerHTML = signIn;
  else fetch('/api/answer', { headers: { Authorization: 'Bearer ' + token } })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((j) => { root.innerHTML = '<h1 data-answer style="font-size:28px;font-weight:600">' + j.answer + '</h1>'; })
    .catch(() => { root.innerHTML = signIn; });
</script></body></html>`;

/** A server that records the headers of every request and serves a tiny app gated on a stored session. */
function server() {
  const seen = [];
  const s = http.createServer((req, res) => {
    seen.push({ url: req.url, headers: req.headers });
    if (req.url === '/api/answer') {
      const ok = req.headers['x-api-key'] === KEY && !req.headers.authorization;
      res.writeHead(ok ? 200 : 401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(ok ? { answer: '3 of 17 lines could make money once freight is priced.' } : { detail: 'no' }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(APP);
  });
  return new Promise((resolve) => s.listen(0, '127.0.0.1', () => resolve({ s, seen, url: `http://127.0.0.1:${s.address().port}` })));
}

(async () => {
  /* ── the plan ── */
  await it('no auth flag, no plan: the old behaviour is unchanged', () => {
    assert.deepStrictEqual(authPlan('https://x.test/p', {}, ENV), { plan: null });
  });
  await it('a credential is read from the named variable, never from the flag', () => {
    const { plan } = authPlan('https://x.test/p', { headerEnv: 'TEST_API_KEY', headerName: 'X-API-Key' }, ENV);
    assert.strictEqual(plan.headers['x-api-key'], KEY);
  });
  await it('a literal value in place of a variable name is refused, and the refusal does not print it', () => {
    const { error } = authPlan('https://x.test/p', { headerEnv: 'sk-live-9f8e7d' }, ENV);
    assert.match(error, /NAME of an environment variable/);
    assert.ok(!error.includes('9f8e7d'), error);
  });
  await it('an unset or empty variable is refused: nothing is sent', () => {
    assert.match(authPlan('https://x.test/p', { headerEnv: 'NOT_SET_ANYWHERE' }, ENV).error, /not set/);
  });
  await it('a credential is never sent over plain http to anything but localhost', () => {
    assert.match(authPlan('http://example.com/p', { headerEnv: 'TEST_API_KEY' }, ENV).error, /https, or localhost only/);
    assert.ok(authPlan('http://127.0.0.1:9/p', { headerEnv: 'TEST_API_KEY' }, ENV).plan);
  });
  await it('--auth-storage-env takes KEY=VARIABLE, never KEY=value', () => {
    assert.match(authPlan('https://x.test/p', { storageEnv: ['tok=abc-123'] }, ENV).error, /does not name a variable/);
    assert.strictEqual(authPlan('https://x.test/p', { storageEnv: ['tok=TEST_API_KEY'] }, ENV).plan.storage.tok, KEY);
  });

  /* ── the header, against two local origins ── */
  const a = await server();
  const b = await server();
  const { plan } = authPlan(
    `${a.url}/product/190`,
    { headerEnv: 'TEST_API_KEY', headerName: 'X-API-Key', dropHeaders: ['Authorization'] },
    ENV,
  );
  await it('same origin: the key arrives and the placeholder bearer does not', async () => {
    const status = await get(`${a.url}/api/answer`, headersFor(plan, `${a.url}/api/answer`, { authorization: 'Bearer placeholder' }));
    assert.strictEqual(status, 200);
    const last = a.seen.at(-1).headers;
    assert.strictEqual(last['x-api-key'], KEY);
    assert.strictEqual(last.authorization, undefined);
  });
  await it('another origin (another port): the key is never sent', async () => {
    await get(`${b.url}/api/answer`, headersFor(plan, `${b.url}/api/answer`, { accept: '*/*' }));
    assert.strictEqual(b.seen.at(-1).headers['x-api-key'], undefined);
  });

  /* ── playwright missing is said, with the install command ── */
  await it('playwright missing: the message carries the install command and says UNCHECKED', () => {
    const saved = process.env.NODE_PATH;
    process.env.NODE_PATH = '';
    const got = loadPlaywright('/nonexistent-dir-for-test');
    process.env.NODE_PATH = saved;
    if (got.playwright) return; // installed in this project: the refusal cannot be observed here
    assert.ok(got.error.includes(PLAYWRIGHT_INSTALL) && /UNCHECKED/.test(got.error), got.error);
  });

  /* ── a real render, where a browser exists ── */
  const pw = loadPlaywright(process.env.PLAYWRIGHT_DIR);
  if (pw.playwright) {
    const floor = { viewport: { width: 1440, height: 900 } };
    const saved = process.env.TEST_API_KEY;
    process.env.TEST_API_KEY = KEY;
    await it('BROWSER — signed out, the sign-in form is reported UNCHECKED, never graded', async () => {
      const got = await snapshotFromUrl(`${a.url}/product/190`, floor, 'light', {}, process.env.PLAYWRIGHT_DIR);
      assert.match(got.error || '', /sign-in form/);
    });
    await it('BROWSER — signed in (key from the env, placeholder session, bearer dropped), the page itself is read', async () => {
      const got = await snapshotFromUrl(
        `${a.url}/product/190`,
        floor,
        'light',
        { headerEnv: 'TEST_API_KEY', headerName: 'X-API-Key', dropHeaders: ['Authorization'], sessionMarker: 'app_token' },
        process.env.PLAYWRIGHT_DIR,
      );
      assert.ok(got.snapshot, got.error);
      assert.match(got.snapshot.answer.text, /^3 of 17 lines/);
    });
    process.env.TEST_API_KEY = saved;
  } else {
    skipped += 2;
    console.log(
      '  SKIPPED 2 browser case(s): playwright is not installed here (set PLAYWRIGHT_DIR to run them). The plan and header cases above ran.',
    );
  }
  a.s.close();
  b.s.close();

  console.log(`rendered-page auth: ${pass} passed, ${failures.length} failed, ${skipped} skipped`);
  for (const f of failures) console.log(`  ✗ ${f}`);
  process.exit(failures.length > 0 ? 1 : 0);
})();
