#!/usr/bin/env node
/*
 * K11 Claims Analytics mock API
 * ------------------------------
 * A small, dependency-free Node.js server that the JMeter learning scripts in
 * this repo run against. It is a safe, local, legal target for load tests.
 *
 * All data is synthetic. There are no real members, providers or claims.
 *
 * It deliberately simulates a limited database connection pool so that you
 * can see a real bottleneck: when more requests arrive than the pool can
 * serve, they queue, response times climb, throughput flattens and, after a
 * timeout, requests fail with HTTP 503.
 *
 * Settings (environment variables):
 *   PORT              default 3000
 *   POOL_SIZE         default 20     simulated DB connections
 *   QUEUE_TIMEOUT_MS  default 5000   max wait for a connection before 503
 *   LATENCY_FACTOR    default 1.0    multiply all simulated work times
 *   METRICS_LOG       default 0      1 = print a metrics line every 5 s
 *   LEAK              default 0      1 = simulate a memory leak (soak demo)
 *
 * Run:  node mock-server/server.js
 */
'use strict';

const http = require('http');
const crypto = require('crypto');
const { URL } = require('url');

const PORT = parseInt(process.env.PORT || '3000', 10);
const POOL_SIZE = parseInt(process.env.POOL_SIZE || '20', 10);
const QUEUE_TIMEOUT_MS = parseInt(process.env.QUEUE_TIMEOUT_MS || '5000', 10);
const LATENCY_FACTOR = parseFloat(process.env.LATENCY_FACTOR || '1.0');
const METRICS_LOG = process.env.METRICS_LOG === '1';
const LEAK = process.env.LEAK === '1';

// ---------------------------------------------------------------------------
// Synthetic reference data
// ---------------------------------------------------------------------------
const PASSWORD = 'learn-jmeter'; // test-only password for every synthetic user
const USERS = new Map();
for (let i = 1; i <= 100; i++) {
  const name = 'analyst' + String(i).padStart(2, '0');
  USERS.set(name, { username: name, displayName: 'Analyst ' + i, role: 'ANALYST' });
}
USERS.set('locked_user', { username: 'locked_user', displayName: 'Locked', role: 'ANALYST', locked: true });

const PROVIDERS = [];
for (let i = 1001; i <= 1020; i++) {
  PROVIDERS.push({ providerId: 'P' + i, providerName: 'Synthetic Provider ' + i });
}
const PROVIDER_BY_ID = new Map(PROVIDERS.map((p) => [p.providerId, p]));

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const tokens = new Map(); // token -> { username, expires }
const sessions = new Map(); // portal session id -> { csrf, username }
const reports = new Map(); // reportId -> report
const exportsById = new Map(); // exportId -> { reportId, createdAt }
const leak = [];

const metrics = {
  startedAt: Date.now(),
  requests: 0,
  completed: 0,
  rejected503: 0,
  errors4xx: 0,
  maxQueueSeen: 0,
};

// ---------------------------------------------------------------------------
// Simulated DB connection pool
// ---------------------------------------------------------------------------
let active = 0;
const waiting = []; // { resolve, reject, timer }

function acquire() {
  return new Promise((resolve, reject) => {
    if (active < POOL_SIZE) {
      active++;
      resolve();
      return;
    }
    const entry = { resolve, reject, timer: null };
    entry.timer = setTimeout(() => {
      const idx = waiting.indexOf(entry);
      if (idx >= 0) waiting.splice(idx, 1);
      reject(new Error('POOL_TIMEOUT'));
    }, QUEUE_TIMEOUT_MS);
    waiting.push(entry);
    if (waiting.length > metrics.maxQueueSeen) metrics.maxQueueSeen = waiting.length;
  });
}

function release() {
  const next = waiting.shift();
  if (next) {
    clearTimeout(next.timer);
    next.resolve(); // hand the connection straight to the next waiter
  } else {
    active--;
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// Hold a pool connection for roughly `baseMs` (with +/-20% jitter).
async function dbWork(baseMs) {
  await acquire();
  try {
    const jitter = 0.8 + Math.random() * 0.4;
    await sleep(Math.max(1, Math.round(baseMs * jitter * LATENCY_FACTOR)));
  } finally {
    release();
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function send(res, status, body, headers = {}) {
  const isString = typeof body === 'string';
  const payload = isString ? body : JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': isString ? headers['Content-Type'] || 'text/html; charset=utf-8' : 'application/json',
    'Content-Length': Buffer.byteLength(payload),
    ...headers,
  });
  res.end(payload);
  if (status >= 400 && status < 500) metrics.errors4xx++;
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (c) => {
      data += c;
      if (data.length > 1e6) req.destroy();
    });
    req.on('end', () => resolve(data));
  });
}

function parseJson(text) {
  try {
    return JSON.parse(text || '{}');
  } catch (e) {
    return null;
  }
}

function parseCookies(req) {
  const out = {};
  (req.headers.cookie || '').split(';').forEach((part) => {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  });
  return out;
}

function newId(prefix) {
  return prefix + '-' + crypto.randomBytes(6).toString('hex');
}

function authUser(req) {
  const h = req.headers.authorization || '';
  if (!h.startsWith('Bearer ')) return null;
  const t = tokens.get(h.slice(7));
  if (!t || t.expires < Date.now()) return null;
  return t.username;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
function validDate(s) {
  if (!DATE_RE.test(s || '')) return null;
  const d = new Date(s + 'T00:00:00Z');
  return isNaN(d.getTime()) ? null : d;
}

// Deterministic pseudo-random numbers so the same query returns the same totals.
function seeded(str) {
  const h = crypto.createHash('sha256').update(str).digest();
  return h.readUInt32BE(0) / 0xffffffff;
}

function buildClaimsSummary(providerId, from, to) {
  const days = Math.round((to - from) / 86400000) + 1;
  const months = [];
  let totalClaims = 0;
  let totalPaidCents = 0;
  const cursor = new Date(Date.UTC(from.getUTCFullYear(), from.getUTCMonth(), 1));
  while (cursor <= to) {
    const key = cursor.toISOString().slice(0, 7);
    const r = seeded(providerId + key);
    const claims = 40 + Math.floor(r * 160);
    const paidCents = claims * (8000 + Math.floor(seeded(key + providerId) * 22000));
    months.push({ month: key, claims, paid: Number((paidCents / 100).toFixed(2)) });
    totalClaims += claims;
    totalPaidCents += paidCents;
    cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  }
  return { days, months, totalClaims, totalPaid: Number((totalPaidCents / 100).toFixed(2)) };
}

function page(title, bodyHtml) {
  return (
    '<!doctype html><html><head><meta charset="utf-8"><title>' +
    title +
    '</title></head><body style="font-family:Segoe UI,Arial,sans-serif;max-width:720px;margin:40px auto">' +
    '<h1>K11 Claims Analytics (mock)</h1>' +
    bodyHtml +
    '<p style="color:#888;font-size:12px">Synthetic data for JMeter practice only.</p></body></html>'
  );
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------
async function handle(req, res) {
  metrics.requests++;
  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname;
  const method = req.method;

  if (LEAK) leak.push(Buffer.alloc(10 * 1024, 1)); // ~10 KB retained per request

  // ----- Health and metrics (not pooled) -----
  if (method === 'GET' && path === '/health') {
    return send(res, 200, { status: 'UP', service: 'k11-claims-mock', version: '1.0.0' });
  }
  if (method === 'GET' && path === '/metrics') {
    const mem = process.memoryUsage();
    return send(res, 200, {
      uptimeSeconds: Math.round((Date.now() - metrics.startedAt) / 1000),
      poolSize: POOL_SIZE,
      poolActive: active,
      poolWaiting: waiting.length,
      maxQueueSeen: metrics.maxQueueSeen,
      requests: metrics.requests,
      completed: metrics.completed,
      rejected503: metrics.rejected503,
      errors4xx: metrics.errors4xx,
      heapUsedMB: Number((mem.heapUsed / 1048576).toFixed(1)),
      rssMB: Number((mem.rss / 1048576).toFixed(1)),
    });
  }

  // ----- Public reference data -----
  if (method === 'GET' && path === '/api/providers') {
    await dbWork(20);
    return send(res, 200, { count: PROVIDERS.length, providers: PROVIDERS });
  }

  // ----- JSON API: login -----
  if (method === 'POST' && path === '/api/auth/login') {
    const body = parseJson(await readBody(req));
    if (!body) return send(res, 400, { error: 'INVALID_JSON' });
    await dbWork(40);
    const user = USERS.get(body.username);
    if (!user || body.password !== PASSWORD) return send(res, 401, { error: 'INVALID_CREDENTIALS' });
    if (user.locked) return send(res, 423, { error: 'ACCOUNT_LOCKED' });
    const token = crypto.randomBytes(24).toString('hex');
    tokens.set(token, { username: user.username, expires: Date.now() + 30 * 60 * 1000 });
    return send(res, 200, {
      token,
      tokenType: 'Bearer',
      expiresIn: 1800,
      user: { username: user.username, displayName: user.displayName, role: user.role },
    });
  }

  // ----- JSON API: everything below needs a Bearer token -----
  if (path.startsWith('/api/')) {
    const username = authUser(req);
    if (!username) return send(res, 401, { error: 'UNAUTHORIZED', message: 'Missing or expired Bearer token' });

    if (method === 'GET' && path === '/api/dashboard') {
      await dbWork(60);
      return send(res, 200, {
        user: username,
        widgets: [
          { id: 'claims-volume', title: 'Claims volume (30 days)', value: 1200 + Math.floor(seeded(username) * 800) },
          { id: 'paid-amount', title: 'Paid amount (30 days)', value: 250000 + Math.floor(seeded('p' + username) * 90000) },
          { id: 'denial-rate', title: 'Denial rate %', value: Number((4 + seeded('d' + username) * 6).toFixed(1)) },
        ],
        favouriteProviders: PROVIDERS.slice(0, 5),
      });
    }

    if (method === 'GET' && path === '/api/reports/claims-summary') {
      const providerId = url.searchParams.get('providerId');
      const from = validDate(url.searchParams.get('from'));
      const to = validDate(url.searchParams.get('to'));
      if (!providerId || !from || !to) {
        return send(res, 400, { error: 'BAD_REQUEST', message: 'providerId, from and to (YYYY-MM-DD) are required' });
      }
      if (from > to) return send(res, 400, { error: 'BAD_REQUEST', message: 'from must be on or before to' });
      const provider = PROVIDER_BY_ID.get(providerId);
      if (!provider) return send(res, 404, { error: 'PROVIDER_NOT_FOUND', providerId });
      const summary = buildClaimsSummary(providerId, from, to);
      // Wider date ranges cost more database time: 120 ms + 15 ms per month.
      await dbWork(120 + 15 * summary.months.length);
      const reportId = newId('rpt');
      reports.set(reportId, { providerId, ...summary });
      if (reports.size > 50000) reports.delete(reports.keys().next().value);
      return send(res, 200, {
        reportId,
        providerId,
        providerName: provider.providerName,
        from: url.searchParams.get('from'),
        to: url.searchParams.get('to'),
        currency: 'USD',
        totalClaims: summary.totalClaims,
        totalPaid: summary.totalPaid,
        byMonth: summary.months,
        generatedAt: new Date().toISOString(),
      });
    }

    if (method === 'POST' && path === '/api/reports/claims-summary/export') {
      const body = parseJson(await readBody(req));
      if (!body || !body.reportId) return send(res, 400, { error: 'BAD_REQUEST', message: 'reportId is required' });
      if (!reports.has(body.reportId)) return send(res, 404, { error: 'REPORT_NOT_FOUND' });
      await dbWork(30);
      const exportId = newId('exp');
      exportsById.set(exportId, { reportId: body.reportId, createdAt: Date.now(), format: body.format || 'CSV' });
      return send(res, 202, { exportId, status: 'QUEUED', statusUrl: '/api/reports/exports/' + exportId });
    }

    let m = path.match(/^\/api\/reports\/exports\/(exp-[0-9a-f]+)$/);
    if (method === 'GET' && m) {
      const exp = exportsById.get(m[1]);
      if (!exp) return send(res, 404, { error: 'EXPORT_NOT_FOUND' });
      await dbWork(10);
      const age = Date.now() - exp.createdAt;
      const status = age < 600 ? 'QUEUED' : age < 1500 ? 'RUNNING' : 'READY';
      const out = { exportId: m[1], status };
      if (status === 'READY') out.downloadUrl = '/api/reports/exports/' + m[1] + '/download';
      return send(res, 200, out);
    }

    m = path.match(/^\/api\/reports\/exports\/(exp-[0-9a-f]+)\/download$/);
    if (method === 'GET' && m) {
      const exp = exportsById.get(m[1]);
      if (!exp) return send(res, 404, { error: 'EXPORT_NOT_FOUND' });
      const rpt = reports.get(exp.reportId);
      await dbWork(80);
      const lines = ['month,claims,paid'].concat(rpt.months.map((r) => r.month + ',' + r.claims + ',' + r.paid.toFixed(2)));
      return send(res, 200, lines.join('\n') + '\n', {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="claims-summary.csv"',
      });
    }

    return send(res, 404, { error: 'NOT_FOUND', path });
  }

  // ----- HTML portal (cookies, CSRF token, form posts: good for recording and regex) -----
  if (method === 'GET' && (path === '/' || path === '/portal' || path === '/portal/login')) {
    const sid = crypto.randomBytes(12).toString('hex');
    const csrf = crypto.randomBytes(16).toString('hex');
    sessions.set(sid, { csrf, username: null });
    return send(
      res,
      200,
      page(
        'Sign in',
        '<h2>Sign in</h2><form method="post" action="/portal/login">' +
          '<input type="hidden" name="_csrf" value="' + csrf + '">' +
          '<p><label>Username <input name="username" value="analyst01"></label></p>' +
          '<p><label>Password <input name="password" type="password" value="' + PASSWORD + '"></label></p>' +
          '<p><button type="submit">Sign in</button></p></form>'
      ),
      { 'Set-Cookie': 'SESSION=' + sid + '; Path=/; HttpOnly' }
    );
  }

  if (method === 'POST' && path === '/portal/login') {
    const form = new URLSearchParams(await readBody(req));
    const sid = parseCookies(req).SESSION;
    const s = sid && sessions.get(sid);
    await dbWork(40);
    if (!s || form.get('_csrf') !== s.csrf) {
      return send(res, 403, page('Forbidden', '<h2>403 - invalid or missing CSRF token</h2>'));
    }
    const user = USERS.get(form.get('username'));
    if (!user || form.get('password') !== PASSWORD || user.locked) {
      return send(res, 401, page('Sign in failed', '<h2>Sign in failed</h2><p><a href="/portal/login">Try again</a></p>'));
    }
    s.username = user.username;
    res.writeHead(302, { Location: '/portal/home', 'Content-Length': 0 });
    return res.end();
  }

  if (path.startsWith('/portal/')) {
    const sid = parseCookies(req).SESSION;
    const s = sid && sessions.get(sid);
    if (!s || !s.username) {
      res.writeHead(302, { Location: '/portal/login', 'Content-Length': 0 });
      return res.end();
    }
    if (method === 'GET' && path === '/portal/home') {
      await dbWork(50);
      const opts = PROVIDERS.map((p) => '<option value="' + p.providerId + '">' + p.providerId + '</option>').join('');
      return send(
        res,
        200,
        page(
          'Home',
          '<h2>Welcome, <span id="welcome-user">' + s.username + '</span></h2>' +
            '<h3>Claims Summary</h3><form method="get" action="/portal/claims-summary">' +
            '<p>Provider <select name="providerId">' + opts + '</select></p>' +
            '<p>From <input name="from" value="2026-01-01"> To <input name="to" value="2026-01-31"></p>' +
            '<p><button type="submit">Run report</button></p></form>' +
            '<p><a href="/portal/logout">Sign out</a></p>'
        )
      );
    }
    if (method === 'GET' && path === '/portal/claims-summary') {
      const providerId = url.searchParams.get('providerId');
      const from = validDate(url.searchParams.get('from'));
      const to = validDate(url.searchParams.get('to'));
      if (!PROVIDER_BY_ID.has(providerId) || !from || !to || from > to) {
        return send(res, 400, page('Bad request', '<h2>Invalid filters</h2>'));
      }
      const summary = buildClaimsSummary(providerId, from, to);
      await dbWork(120 + 15 * summary.months.length);
      const rows = summary.months.map((r) => '<tr><td>' + r.month + '</td><td>' + r.claims + '</td><td>' + r.paid.toFixed(2) + '</td></tr>').join('');
      return send(
        res,
        200,
        page(
          'Claims Summary',
          '<h2>Claims Summary for ' + providerId + '</h2>' +
            '<p>Total claims: <b id="total-claims">' + summary.totalClaims + '</b></p>' +
            '<p>Total paid: <b id="total-paid">$' + summary.totalPaid.toLocaleString('en-US', { minimumFractionDigits: 2 }) + '</b></p>' +
            '<table border="1" cellpadding="4"><tr><th>Month</th><th>Claims</th><th>Paid</th></tr>' + rows + '</table>' +
            '<p><a href="/portal/home">Back</a></p>'
        )
      );
    }
    if (method === 'GET' && path === '/portal/logout') {
      sessions.delete(sid);
      res.writeHead(302, { Location: '/portal/login', 'Content-Length': 0 });
      return res.end();
    }
  }

  return send(res, 404, { error: 'NOT_FOUND', path });
}

const server = http.createServer((req, res) => {
  handle(req, res)
    .then(() => {
      metrics.completed++;
    })
    .catch((err) => {
      if (err && err.message === 'POOL_TIMEOUT') {
        metrics.rejected503++;
        if (!res.headersSent) send(res, 503, { error: 'SERVICE_UNAVAILABLE', message: 'No database connection available (pool exhausted)' }, { 'Retry-After': '1' });
        return;
      }
      console.error(err);
      if (!res.headersSent) send(res, 500, { error: 'INTERNAL_ERROR' });
    });
});
server.keepAliveTimeout = 65000;

// Clean up expired tokens and old exports every minute.
setInterval(() => {
  const now = Date.now();
  for (const [t, v] of tokens) if (v.expires < now) tokens.delete(t);
  for (const [id, e] of exportsById) if (now - e.createdAt > 10 * 60 * 1000) exportsById.delete(id);
  if (sessions.size > 50000) sessions.clear();
}, 60000).unref();

if (METRICS_LOG) {
  setInterval(() => {
    const mem = process.memoryUsage();
    console.log(
      new Date().toISOString() +
        ' active=' + active + '/' + POOL_SIZE +
        ' waiting=' + waiting.length +
        ' requests=' + metrics.requests +
        ' rejected503=' + metrics.rejected503 +
        ' heapMB=' + (mem.heapUsed / 1048576).toFixed(1)
    );
  }, 5000).unref();
}

server.listen(PORT, () => {
  console.log('K11 Claims Analytics mock API listening on http://localhost:' + PORT);
  console.log('POOL_SIZE=' + POOL_SIZE + ' QUEUE_TIMEOUT_MS=' + QUEUE_TIMEOUT_MS + ' LATENCY_FACTOR=' + LATENCY_FACTOR + (LEAK ? ' LEAK=on' : ''));
});

process.on('SIGINT', () => process.exit(0));
process.on('SIGTERM', () => process.exit(0));
