import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { access } from "node:fs/promises";
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";
import { once } from "node:events";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const DEFAULT_VIEWPORTS = [
  { name: "desktop", width: 1366, height: 900, mobile: false },
  { name: "mobile", width: 390, height: 844, mobile: true },
];

const DEFAULT_FORBIDDEN = ["Traceback", "Internal Server Error"];

const args = parseArgs(process.argv.slice(2));
const baseUrl = (args.baseUrl ?? process.env.LAND_DD_UI_SMOKE_BASE_URL ?? "http://127.0.0.1:8000")
  .replace(/\/+$/, "");
const chromePath = args.chromePath ?? process.env.LAND_DD_CHROME_PATH ?? await findChromePath();
const screenshotDir = args.screenshotDir ?? process.env.LAND_DD_UI_SMOKE_SCREENSHOT_DIR ?? "";
const runMode = args.mode ?? process.env.LAND_DD_UI_SMOKE_MODE ?? "headless";
const apiKey = args.apiKey ?? process.env.LAND_DD_UI_SMOKE_API_KEY ?? "";
const reviewerId = args.reviewerId ?? process.env.LAND_DD_UI_SMOKE_REVIEWER_ID ?? "";
const reviewerToken = args.reviewerToken ?? process.env.LAND_DD_UI_SMOKE_REVIEWER_TOKEN ?? "";
const timeoutMs = Number(args.timeoutMs ?? process.env.LAND_DD_UI_SMOKE_TIMEOUT_MS ?? "10000");
const emitJson = Boolean(args.json);

if (!chromePath) {
  fail("Chrome executable not found. Set --chrome-path or LAND_DD_CHROME_PATH.");
}
if ((reviewerId && !reviewerToken) || (!reviewerId && reviewerToken)) {
  fail("--reviewer-id and --reviewer-token must be supplied together.");
}
if (!["headless", "headed", "both"].includes(runMode)) {
  fail("--mode must be headless, headed, or both.");
}
if (screenshotDir) {
  await mkdir(screenshotDir, { recursive: true });
}

const modes = runMode === "both" ? ["headless", "headed"] : [runMode];
const cookies = [];
if (apiKey) {
  cookies.push(...await loginForCookies(`${baseUrl}/ui/auth`, { api_key: apiKey }));
}
if (reviewerId) {
  cookies.push(
    ...await loginForCookies(`${baseUrl}/ui/auth/reviewer`, {
      reviewer_id: reviewerId,
      reviewer_token: reviewerToken,
    }),
  );
}

const routes = buildRoutes({ apiKey: Boolean(apiKey), reviewerSession: Boolean(reviewerId) });
const runResults = [];

for (const mode of modes) {
  for (const viewport of DEFAULT_VIEWPORTS) {
    runResults.push(await runChromeSmoke({ mode, viewport, routes, cookies }));
  }
}

const ok = runResults.every((run) => run.ok);
if (emitJson) {
  console.log(JSON.stringify({ ok, baseUrl, runs: runResults }, null, 2));
} else {
  for (const run of runResults) {
    console.log(`${run.ok ? "ok" : "fail"}: ${run.mode}-${run.viewport}`);
    for (const page of run.pages) {
      console.log(`  ${page.ok ? "ok" : "fail"}: ${page.label} ${page.path}`);
      for (const failure of page.failures) {
        console.log(`    - ${failure}`);
      }
    }
  }
}
process.exit(ok ? 0 : 1);

async function runChromeSmoke({ mode, viewport, routes, cookies }) {
  const port = await reserveDebugPort(mode, viewport.name);
  const profileDir = await mkdtemp(join(tmpdir(), "land-dd-ui-smoke-"));
  const chrome = spawnChrome({ mode, port, profileDir, viewport });
  let chromeError = "";
  chrome.stderr.on("data", (chunk) => {
    chromeError += chunk.toString();
  });
  try {
    await waitForChrome(port, () => chromeError);
    const target = await newPage(port, `${baseUrl}/ui/`);
    const cdp = await connectCdp(target.webSocketDebuggerUrl);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Network.enable");
    await setViewport(cdp, viewport);
    for (const cookie of cookies) {
      await cdp.send("Network.setCookie", {
        url: baseUrl,
        name: cookie.name,
        value: cookie.value,
        path: cookie.path || "/ui",
        httpOnly: cookie.httpOnly,
        sameSite: cookie.sameSite,
        secure: cookie.secure,
      });
    }

    const pages = [];
    for (const route of routes) {
      pages.push(await checkPage(cdp, route, mode, viewport));
    }
    await cdp.send("Browser.close").catch(() => undefined);
    cdp.close();
    return {
      mode,
      viewport: viewport.name,
      ok: pages.every((page) => page.ok),
      pages,
    };
  } finally {
    await stopChrome(chrome);
    await removeProfile(profileDir);
  }
}

function spawnChrome({ mode, port, profileDir, viewport }) {
  const chromeArgs = [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--disable-first-run-ui",
    "--disable-default-apps",
    "--hide-crash-restore-bubble",
    `--window-size=${viewport.width},${viewport.height}`,
  ];
  if (mode === "headless") {
    chromeArgs.push("--headless=new", "--disable-gpu");
  }
  return spawn(chromePath, chromeArgs, { stdio: ["ignore", "ignore", "pipe"] });
}

function buildRoutes({ apiKey, reviewerSession }) {
  return [
    {
      label: "home",
      path: "/ui/",
      required: ["Land Diligence"],
    },
    {
      label: "report-runs",
      path: "/ui/report-runs",
      required: ["Report Runs", "Compare Selected"],
      forbidden: ["<script>"],
    },
    {
      label: "connector-review-queue",
      path: "/ui/connector-review-queue",
      required: ["Connector Review Queue"],
    },
    {
      label: "api-key-auth",
      path: "/ui/auth",
      required: ['name="api_key"'],
    },
    {
      label: "reviewer-auth",
      path: "/ui/auth/reviewer",
      required: reviewerSession
        ? ["Reviewer session"]
        : ['name="reviewer_id"', 'name="reviewer_token"'],
    },
    {
      label: "operations",
      path: "/ui/operations",
      required: reviewerSession
        ? ["Operations Dashboard", "Using reviewer session"]
        : ["Operations Dashboard", 'name="reviewer_token"'],
      forbidden: reviewerSession ? ['name="reviewer_token"'] : [],
    },
  ];
}

async function checkPage(cdp, route, mode, viewport) {
  const failures = [];
  const path = route.path;
  await navigate(cdp, `${baseUrl}${path}`);
  const result = await cdp.send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression: `
      (() => ({
        title: document.title,
        url: location.href,
        contentType: document.contentType,
        hasViewport: Boolean(document.querySelector('meta[name="viewport"]')),
        text: document.body?.innerText ?? "",
        html: document.documentElement?.outerHTML ?? "",
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth
      }))()
    `,
  });
  const value = result.result.value;
  if (!value.text.trim()) {
    failures.push("empty body");
  }
  if (!value.hasViewport) {
    failures.push("missing viewport meta");
  }
  if (value.contentType !== "text/html") {
    failures.push(`expected text/html document, got ${value.contentType}`);
  }
  for (const text of route.required ?? []) {
    if (!value.html.includes(text) && !value.text.includes(text)) {
      failures.push(`missing required text: ${text}`);
    }
  }
  for (const text of [...DEFAULT_FORBIDDEN, ...(route.forbidden ?? [])]) {
    if (value.html.includes(text) || value.text.includes(text)) {
      failures.push(`found forbidden text: ${text}`);
    }
  }
  if (value.scrollWidth > value.clientWidth + 1) {
    failures.push(`page-level horizontal overflow: ${value.scrollWidth} > ${value.clientWidth}`);
  }
  const screenshotFile = await maybeCaptureScreenshot(cdp, route.label, mode, viewport.name);
  return {
    label: route.label,
    path,
    ok: failures.length === 0,
    title: value.title,
    clientWidth: value.clientWidth,
    scrollWidth: value.scrollWidth,
    screenshot: screenshotFile,
    failures,
  };
}

async function maybeCaptureScreenshot(cdp, label, mode, viewportName) {
  if (!screenshotDir) {
    return null;
  }
  const shot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: true,
    fromSurface: true,
  });
  const filename = `ui-smoke-${label}-${mode}-${viewportName}.png`;
  const path = join(screenshotDir, filename);
  await writeFile(path, Buffer.from(shot.data, "base64"));
  return path;
}

async function setViewport(cdp, viewport) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.mobile ? 2 : 1,
    mobile: Boolean(viewport.mobile),
  });
}

async function navigate(cdp, url) {
  await cdp.send("Page.navigate", { url });
  await waitForLoad(cdp);
}

async function waitForLoad(cdp) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const state = await cdp.send("Runtime.evaluate", {
      returnByValue: true,
      expression: "document.readyState",
    });
    if (state.result.value === "complete" || state.result.value === "interactive") {
      return;
    }
    await delay(100);
  }
  throw new Error("Timed out waiting for document readiness");
}

async function waitForChrome(port, errorText) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await httpJson(`http://127.0.0.1:${port}/json/version`);
      return;
    } catch {
      await delay(150);
    }
  }
  throw new Error(`Chrome did not start on port ${port}: ${errorText()}`);
}

async function newPage(port, url) {
  return await httpJson(
    `http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`,
    "PUT",
  );
}

function connectCdp(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let nextId = 1;
    const pending = new Map();
    const cdp = {
      send(method, params = {}) {
        const id = nextId++;
        ws.send(JSON.stringify({ id, method, params }));
        return new Promise((res, rej) => {
          pending.set(id, { resolve: res, reject: rej, method });
        });
      },
      close() {
        ws.close();
      },
    };
    ws.addEventListener("open", () => resolve(cdp));
    ws.addEventListener("error", reject);
    ws.addEventListener("message", (raw) => {
      const msg = JSON.parse(raw.data);
      if (!msg.id || !pending.has(msg.id)) {
        return;
      }
      const item = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) {
        item.reject(new Error(`${item.method}: ${msg.error.message}`));
      } else {
        item.resolve(msg.result);
      }
    });
  });
}

async function loginForCookies(url, fields) {
  const response = await httpForm(url, fields);
  const setCookie = response.headers["set-cookie"] ?? [];
  return setCookie.flatMap(parseSetCookie);
}

function parseSetCookie(header) {
  const lines = Array.isArray(header) ? header : [header];
  return lines.flatMap((line) => {
    if (!line) {
      return [];
    }
    const parts = line.split(";").map((part) => part.trim());
    const [name, ...valueParts] = parts[0].split("=");
    if (!name || valueParts.length === 0) {
      return [];
    }
    const attrs = new Map(
      parts.slice(1).map((part) => {
        const [key, ...value] = part.split("=");
        return [key.toLowerCase(), value.join("=")];
      }),
    );
    const sameSite = (attrs.get("samesite") || "Lax").replace(/^./, (c) => c.toUpperCase());
    return [{
      name,
      value: valueParts.join("="),
      path: attrs.get("path") || "/ui",
      httpOnly: attrs.has("httponly"),
      sameSite,
      secure: attrs.has("secure"),
    }];
  });
}

function httpJson(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = httpRequest(url, { method }, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        if (!res.statusCode || res.statusCode >= 400) {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
          return;
        }
        resolve(JSON.parse(body));
      });
    });
    req.on("error", reject);
    req.end();
  });
}

function httpForm(url, fields) {
  const body = new URLSearchParams(fields).toString();
  const client = url.startsWith("https:") ? httpsRequest : httpRequest;
  return new Promise((resolve, reject) => {
    const req = client(
      url,
      {
        method: "POST",
        headers: {
          "content-type": "application/x-www-form-urlencoded",
          "content-length": Buffer.byteLength(body),
        },
      },
      (res) => {
        let responseBody = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          responseBody += chunk;
        });
        res.on("end", () => {
          if (!res.statusCode || res.statusCode >= 400) {
            reject(new Error(`POST ${url} returned HTTP ${res.statusCode}: ${responseBody}`));
            return;
          }
          resolve({ headers: res.headers, body: responseBody });
        });
      },
    );
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

async function reserveDebugPort(mode, viewportName) {
  void mode;
  void viewportName;
  return await findFreePort();
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => {
        if (!address || typeof address === "string") {
          reject(new Error("Could not reserve a TCP port for Chrome"));
        } else {
          resolve(address.port);
        }
      });
    });
  });
}

async function stopChrome(chrome) {
  if (chrome.exitCode !== null) {
    return;
  }
  chrome.kill();
  try {
    await Promise.race([once(chrome, "close"), delay(2000)]);
  } catch {
    // Cleanup continues below; a process may already be gone on Windows.
  }
}

async function removeProfile(profileDir) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      await rm(profileDir, { recursive: true, force: true });
      return;
    } catch (error) {
      if (!["EBUSY", "EPERM", "ENOTEMPTY"].includes(error.code) || attempt === 4) {
        throw error;
      }
      await delay(250 * (attempt + 1));
    }
  }
}

async function findChromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA ?? ""}/Google/Chrome/Application/chrome.exe`,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      // Try the next known installation path.
    }
  }
  return "";
}

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") {
      parsed.json = true;
    } else if (arg === "--base-url") {
      parsed.baseUrl = argv[++index];
    } else if (arg === "--chrome-path") {
      parsed.chromePath = argv[++index];
    } else if (arg === "--screenshot-dir") {
      parsed.screenshotDir = argv[++index];
    } else if (arg === "--mode") {
      parsed.mode = argv[++index];
    } else if (arg === "--api-key") {
      parsed.apiKey = argv[++index];
    } else if (arg === "--reviewer-id") {
      parsed.reviewerId = argv[++index];
    } else if (arg === "--reviewer-token") {
      parsed.reviewerToken = argv[++index];
    } else if (arg === "--timeout-ms") {
      parsed.timeoutMs = argv[++index];
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      fail(`Unknown argument: ${arg}`);
    }
  }
  return parsed;
}

function printHelp() {
  console.log(`Usage: node scripts/ui_browser_smoke.mjs [options]

Options:
  --base-url URL          Running land_dd base URL (default: env or http://127.0.0.1:8000)
  --chrome-path PATH      Chrome/Chromium executable path (default: auto-detect)
  --mode MODE             headless, headed, or both (default: headless)
  --api-key VALUE         Optional UI API key for API-key-locked runtimes
  --reviewer-id VALUE     Optional reviewer id for reviewer-session UI checks
  --reviewer-token VALUE  Optional reviewer token for reviewer-session UI checks
  --screenshot-dir PATH   Optional ignored output directory for screenshots
  --timeout-ms VALUE      Per-operation timeout in milliseconds (default: 10000)
  --json                  Emit JSON result
`);
}

function fail(message) {
  if (emitJson) {
    console.log(JSON.stringify({ ok: false, error: message }, null, 2));
  } else {
    console.error(`ui browser smoke failed: ${message}`);
  }
  process.exit(1);
}
