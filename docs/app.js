/* Jobseeker PWA — no framework, no build, no tracking. */
(() => {
  "use strict";

  const KEY = "jobseeker.v1";
  const SYNC_KEY = "jobseeker.sync";
  const PREF_KEY = "jobseeker.prefs";
  const SEEN_KEY = "jobseeker.lastVisit";
  const FOLLOW_UP_DAYS = 7;
  const STATUSES = ["saved", "applied", "interview", "offer", "rejected"];
  const LABEL = { saved: "Saved", applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected" };

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  // ---------- storage (always guarded: private mode / blocked storage) ----------
  const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* ignore */ } };

  let store = load(KEY, { v: 1, items: {} });
  let prefs = Object.assign({ elig: "eligible", sort: "score", age: "0", source: "", minScore: 0, hideTracked: true, newOnly: false, theme: "" }, load(PREF_KEY, {}));
  let sync = load(SYNC_KEY, { token: "", gistId: "", last: "" });
  const lastVisit = load(SEEN_KEY, null);
  let data = { jobs: [] };
  let trackerFilter = "";

  // ---------- utils ----------
  const now = () => new Date().toISOString();
  const days = (iso) => iso ? (Date.now() - new Date(iso).getTime()) / 864e5 : null;
  function ago(iso) {
    const d = days(iso);
    if (d == null) return "date ?";
    if (d < 1 / 24) return "just now";
    if (d < 1) return Math.round(d * 24) + "h ago";
    if (d < 60) return Math.round(d) + "d ago";
    return new Date(iso).toLocaleDateString();
  }
  function toast(msg) {
    const t = document.createElement("div");
    t.className = "toast"; t.textContent = msg; document.body.append(t);
    setTimeout(() => t.remove(), 2200);
  }
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
    }
    for (const k of kids) if (k != null) e.append(k);
    return e;
  };
  const safeUrl = (u) => /^https?:\/\//i.test(u || "") ? u : "#";
  const repoInfo = () => {
    // https://<user>.github.io/<repo>/  →  github.com/<user>/<repo>
    const m = location.hostname.match(/^([^.]+)\.github\.io$/);
    const repo = location.pathname.split("/").filter(Boolean)[0];
    return m && repo ? `https://github.com/${m[1]}/${repo}` : "https://github.com/kariyu42/jobseeker";
  };

  // ---------- tracker state ----------
  const item = (id) => { const it = store.items[id]; return it && it.status !== "removed" ? it : null; };
  function setStatus(job, status) {
    const prev = store.items[job.id] || {};
    const it = Object.assign({}, prev, {
      status, updated_at: now(),
      job: prev.job || { title: job.title, company: job.company, url: job.url, eligibility: job.eligibility, elig_reason: job.elig_reason, salary: job.salary },
    });
    if (status === "applied" && !it.applied_at) it.applied_at = now();
    store.items[job.id] = it;
    persist();
  }
  function persist() {
    save(KEY, store);
    updateBadge();
    if (sync.token) scheduleSync();
  }

  // ---------- theme ----------
  function applyTheme() {
    if (prefs.theme) document.documentElement.dataset.theme = prefs.theme;
    else delete document.documentElement.dataset.theme;
  }
  $("#themeBtn").addEventListener("click", () => {
    const dark = prefs.theme ? prefs.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    prefs.theme = dark ? "light" : "dark";
    save(PREF_KEY, prefs); applyTheme();
  });

  // ---------- tabs ----------
  function show(view) {
    $$(".tabs button").forEach(b => b.classList.toggle("on", b.dataset.view === view));
    $$(".view").forEach(v => v.classList.toggle("active", v.id === "view-" + view));
    if (view === "tracker") renderTracker();
    if (view === "settings") renderSettings();
    window.scrollTo(0, 0);
  }
  $$(".tabs button").forEach(b => b.addEventListener("click", () => show(b.dataset.view)));

  // ---------- filters ----------
  function bindFilters() {
    if (matchMedia("(min-width: 720px)").matches) $("#moreFilters").open = true;
    $$(".seg button").forEach(b => {
      b.classList.toggle("on", b.dataset.elig === prefs.elig);
      b.addEventListener("click", () => { prefs.elig = b.dataset.elig; $$(".seg button").forEach(x => x.classList.toggle("on", x === b)); changed(); });
    });
    $("#sort").value = prefs.sort; $("#age").value = prefs.age;
    $("#minScore").value = prefs.minScore; $("#minScoreOut").textContent = prefs.minScore;
    $("#hideTracked").checked = prefs.hideTracked; $("#newOnly").checked = prefs.newOnly;
    $("#sort").onchange = e => { prefs.sort = e.target.value; changed(); };
    $("#age").onchange = e => { prefs.age = e.target.value; changed(); };
    $("#source").onchange = e => { prefs.source = e.target.value; changed(); };
    $("#minScore").oninput = e => { prefs.minScore = +e.target.value; $("#minScoreOut").textContent = e.target.value; changed(); };
    $("#hideTracked").onchange = e => { prefs.hideTracked = e.target.checked; changed(); };
    $("#newOnly").onchange = e => { prefs.newOnly = e.target.checked; changed(); };
    let t; $("#q").oninput = () => { clearTimeout(t); t = setTimeout(renderJobs, 150); };
  }
  function changed() { save(PREF_KEY, prefs); renderJobs(); }

  const isNew = (j) => lastVisit ? j.first_seen > lastVisit : days(j.first_seen) < 1;

  function filtered() {
    const q = $("#q").value.trim().toLowerCase();
    const maxAge = +prefs.age;
    let list = data.jobs.filter(j => {
      if (prefs.elig === "eligible" && j.eligibility !== "eligible") return false;
      if (prefs.elig === "unclear" && j.eligibility === "not_eligible") return false;
      if (j.score < prefs.minScore) return false;
      if (prefs.source && !(j.sources || [j.source]).includes(prefs.source)) return false;
      if (maxAge && (days(j.posted_at || j.first_seen) ?? 0) > maxAge) return false;
      const it = store.items[j.id];
      if (it && it.status === "hidden") return false;
      if (prefs.hideTracked && item(j.id)) return false;
      if (prefs.newOnly && !isNew(j)) return false;
      if (q) {
        const hay = [j.title, j.company, j.location, (j.skills || []).join(" "), (j.tags || []).join(" "), j.description].join(" ").toLowerCase();
        if (!q.split(/\s+/).every(w => hay.includes(w))) return false;
      }
      return true;
    });
    const date = j => j.posted_at || j.first_seen || "";
    list.sort(prefs.sort === "date" ? (a, b) => date(b).localeCompare(date(a)) : (a, b) => b.score - a.score || date(b).localeCompare(date(a)));
    return list;
  }

  // ---------- jobs view ----------
  const ELIG_ICON = { eligible: "✅", unclear: "⚠️", not_eligible: "❌" };
  let renderLimit = 60;

  function jobCard(j) {
    const c = $("#tpl-job").content.firstElementChild.cloneNode(true);
    if (j.active === false) c.classList.add("inactive");
    const sc = $(".score", c); sc.textContent = j.score;
    sc.classList.add(j.score >= 70 ? "hi" : j.score >= 45 ? "mid" : "lo");
    const a = $(".title", c); a.textContent = j.title; a.href = safeUrl(j.url);
    $(".meta", c).textContent = [j.company, ago(j.posted_at || j.first_seen), (j.sources || [j.source]).join(" + ")].join(" · ");
    const e = $(".elig", c); e.classList.add(j.eligibility);
    const showLoc = j.location && !(j.elig_reason || "").toLowerCase().includes(j.location.toLowerCase());
    e.textContent = `${ELIG_ICON[j.eligibility] || ""} ${j.elig_reason || ""}${showLoc ? " — " + j.location.slice(0, 80) : ""}`;
    const chips = $(".chips", c);
    if (isNew(j)) chips.append(el("span", { class: "chip new" }, "NEW"));
    if (j.active === false) chips.append(el("span", { class: "chip warn" }, "no longer listed"));
    if (j.salary) chips.append(el("span", { class: "chip money" }, j.salary));
    if (j.contractor) chips.append(el("span", { class: "chip" }, "contractor/EOR ok"));
    for (const s of (j.skills || []).slice(0, 8)) chips.append(el("span", { class: "chip skill" }, s));
    $(".desc", c).textContent = j.description || "No description.";
    $(".open", c).href = safeUrl(j.url);
    const it = item(j.id);
    const sv = $(".save", c), ap = $(".apply", c);
    if (it?.status === "saved") { sv.classList.add("on"); sv.textContent = "★ Saved"; }
    if (it && it.status !== "saved") { ap.classList.add("on"); ap.textContent = "✓ " + LABEL[it.status]; }
    sv.onclick = () => { setStatus(j, it?.status === "saved" ? "removed" : "saved"); renderJobs(); toast(it?.status === "saved" ? "Removed" : "Saved to tracker"); };
    ap.onclick = () => { setStatus(j, "applied"); renderJobs(); toast("Marked applied — follow up in " + FOLLOW_UP_DAYS + " days"); };
    $(".hide", c).onclick = () => { setStatus(j, "hidden"); renderJobs(); toast("Hidden"); };
    return c;
  }

  function renderJobs() {
    const list = filtered();
    const box = $("#jobs"); box.replaceChildren();
    const total = data.jobs.length;
    $("#count").textContent = `${list.length} of ${total} jobs` + (data.counts ? ` · ✅ ${data.counts.eligible} can hire you · ⚠️ ${data.counts.unclear} unclear · ❌ ${data.counts.not_eligible} can't` : "");
    if (!total) {
      box.append(el("div", { class: "empty" }, data.generated_at ? "No jobs matched your config yet." : "No jobs fetched yet. Run the “Fetch jobs” workflow on GitHub (Actions tab), or wait for the next scheduled run."));
      return;
    }
    if (!list.length) { box.append(el("div", { class: "empty" }, "Nothing matches these filters. Try “+ Unclear” or lower the min match.")); return; }
    const frag = document.createDocumentFragment();
    list.slice(0, renderLimit).forEach(j => frag.append(jobCard(j)));
    box.append(frag);
    if (list.length > renderLimit) {
      box.append(el("button", { class: "btn", onclick: () => { renderLimit += 60; renderJobs(); } }, `Show more (${list.length - renderLimit})`));
    }
  }

  // ---------- tracker view ----------
  const needsFollowUp = (it) => it.status === "applied" && days(it.applied_at) >= FOLLOW_UP_DAYS && (!it.followed_up_at || days(it.followed_up_at) >= FOLLOW_UP_DAYS);
  function updateBadge() {
    const n = Object.values(store.items).filter(it => it.status !== "removed" && needsFollowUp(it)).length;
    const b = $("#trkBadge"); b.hidden = !n; b.textContent = n;
  }

  function renderTracker() {
    const items = Object.entries(store.items).filter(([, it]) => STATUSES.includes(it.status));
    const pipe = $("#pipeline"); pipe.replaceChildren();
    for (const s of STATUSES) {
      const n = items.filter(([, it]) => it.status === s).length;
      pipe.append(el("button", { class: trackerFilter === s ? "on" : "", onclick: () => { trackerFilter = trackerFilter === s ? "" : s; renderTracker(); } }, el("b", {}, String(n)), LABEL[s]));
    }
    const box = $("#tracker"); box.replaceChildren();
    const shown = items.filter(([, it]) => !trackerFilter || it.status === trackerFilter)
      .sort(([, a], [, b]) => (needsFollowUp(b) - needsFollowUp(a)) || (b.updated_at || "").localeCompare(a.updated_at || ""));
    if (!shown.length) { box.append(el("div", { class: "empty" }, "Nothing here yet. Save or mark jobs as applied from the Jobs tab.")); return; }
    const byId = Object.fromEntries(data.jobs.map(j => [j.id, j]));
    for (const [id, it] of shown) {
      const j = byId[id] || it.job || {};
      const sel = el("select", { "aria-label": "Status" });
      for (const s of STATUSES) { const o = el("option", { value: s }, LABEL[s]); if (s === it.status) o.selected = true; sel.append(o); }
      sel.onchange = () => { setStatus({ id, ...j }, sel.value); renderTracker(); };
      const notes = el("textarea", { placeholder: "Notes: contact name, salary discussed, next step…" });
      notes.value = it.notes || "";
      notes.onchange = () => { store.items[id].notes = notes.value; store.items[id].updated_at = now(); persist(); };
      const meta = [j.company, it.applied_at ? "applied " + ago(it.applied_at) : "saved " + ago(it.updated_at), j.salary].filter(Boolean).join(" · ");
      const card = el("article", { class: "card" },
        el("h3", {}, el("a", { href: safeUrl(j.url), target: "_blank", rel: "noopener" }, j.title || "(job)")),
        el("p", { class: "meta small muted" }, meta),
        needsFollowUp(it) ? el("p", { class: "small followup" }, `⏰ No reply after ${Math.floor(days(it.applied_at))} days — send a short follow-up (or message an engineer there).`) : null,
        el("div", { class: "trk-row" }, sel,
          el("a", { class: "btn", href: safeUrl(j.url), target: "_blank", rel: "noopener" }, "Open ↗"),
          needsFollowUp(it) ? el("button", { class: "btn", onclick: () => { store.items[id].followed_up_at = now(); store.items[id].updated_at = now(); persist(); renderTracker(); } }, "Followed up") : null,
          el("button", { class: "btn hide", title: "Remove from tracker", onclick: () => { setStatus({ id, ...j }, "removed"); renderTracker(); } }, "✕")),
        notes);
      box.append(card);
    }
  }

  // ---------- settings ----------
  function renderSettings() {
    $("#ghToken").value = sync.token ? "••••••••" + sync.token.slice(-4) : "";
    $("#gistId").value = sync.gistId || "";
    $("#syncStatus").textContent = sync.token ? (sync.last ? "Last synced " + ago(sync.last) : "Not synced yet") : "Sync is off.";
    const p = data.profile || {};
    $("#profile").replaceChildren(el("table", {}, ...[
      ["Lives in", p.home_country], ["Can work in", (p.work_authorization || []).join(", ")],
      ["Would live in", (p.would_live_in || []).join(", ")],
      ["Hours", p.timezone_min != null ? `UTC${fmtOff(p.timezone_min)} … UTC${fmtOff(p.timezone_max)}` : ""], ["Level", p.level],
    ].map(([k, v]) => el("tr", {}, el("th", {}, k), el("td", {}, v || "—")))));
    const rows = Object.entries(data.sources || {}).map(([n, s]) =>
      el("tr", {}, el("td", {}, n), el("td", {}, `${s.kept} kept / ${s.raw} fetched`), el("td", { class: s.error ? "err" : "" }, s.error ? "failed" : "ok")));
    $("#sources").replaceChildren(rows.length ? el("table", {}, ...rows) : el("p", { class: "muted" }, "No run yet."));
    const repo = repoInfo();
    $("#cfgLink").href = repo + "/edit/HEAD/config.yml";
    $("#guideLink").href = repo + "/blob/HEAD/GUIDE.md";
  }
  const fmtOff = (n) => (n >= 0 ? "+" : "") + n;

  $("#exportBtn").onclick = () => {
    const blob = new Blob([JSON.stringify(store, null, 1)], { type: "application/json" });
    const a = el("a", { href: URL.createObjectURL(blob), download: `jobseeker-tracker-${new Date().toISOString().slice(0, 10)}.json` });
    document.body.append(a); a.click(); a.remove();
    toast("Exported");
  };
  $("#importFile").onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    try {
      const incoming = JSON.parse(await f.text());
      if (!incoming.items) throw new Error("not a jobseeker export");
      const n = mergeInto(incoming);
      persist(); renderJobs(); toast(`Imported (${n} updated)`);
    } catch (err) { toast("Import failed: " + err.message); }
    e.target.value = "";
  };

  /** Newest edit per job wins. Returns number of entries changed. */
  function mergeInto(incoming) {
    let n = 0;
    for (const [id, it] of Object.entries(incoming.items || {})) {
      const mine = store.items[id];
      if (!mine || (it.updated_at || "") > (mine.updated_at || "")) { store.items[id] = it; n++; }
    }
    return n;
  }

  // ---------- gist sync ----------
  const GIST_FILE = "jobseeker-tracker.json";
  let syncTimer;
  function scheduleSync() { clearTimeout(syncTimer); syncTimer = setTimeout(() => doSync(false), 2500); }

  async function gh(path, opts = {}) {
    const r = await fetch("https://api.github.com" + path, {
      ...opts,
      headers: { Authorization: "Bearer " + sync.token, Accept: "application/vnd.github+json", "Content-Type": "application/json" },
    });
    if (!r.ok) throw new Error(`GitHub ${r.status}${r.status === 401 ? " (bad token)" : r.status === 404 ? " (gist not found)" : ""}`);
    return r.json();
  }

  async function doSync(loud = true) {
    if (!sync.token) { if (loud) toast("Add a token first"); return; }
    $("#syncStatus").textContent = "Syncing…";
    try {
      if (sync.gistId) {
        const g = await gh("/gists/" + sync.gistId);
        const f = g.files[GIST_FILE];
        if (f) {
          const content = f.truncated ? await (await fetch(f.raw_url)).text() : f.content;
          mergeInto(JSON.parse(content || "{}"));
        }
        await gh("/gists/" + sync.gistId, { method: "PATCH", body: JSON.stringify({ files: { [GIST_FILE]: { content: JSON.stringify(store) } } }) });
      } else {
        const g = await gh("/gists", { method: "POST", body: JSON.stringify({ description: "jobseeker tracker sync", public: false, files: { [GIST_FILE]: { content: JSON.stringify(store) } } }) });
        sync.gistId = g.id;
        if (loud) toast("Gist created — copy the Gist ID to your other device");
      }
      sync.last = now(); save(SYNC_KEY, sync); save(KEY, store);
      updateBadge();
      if ($("#view-jobs").classList.contains("active")) renderJobs();
      if ($("#view-tracker").classList.contains("active")) renderTracker();
      if (loud) toast("Synced");
    } catch (err) {
      if (loud) toast("Sync failed: " + err.message);
      $("#syncStatus").textContent = "Sync failed: " + err.message;
      return;
    }
    if ($("#view-settings").classList.contains("active")) renderSettings();
  }

  $("#syncBtn").onclick = () => {
    const tok = $("#ghToken").value.trim();
    if (tok && !tok.startsWith("••")) sync.token = tok;
    sync.gistId = $("#gistId").value.trim();
    save(SYNC_KEY, sync);
    doSync(true);
  };
  $("#syncOff").onclick = () => { sync = { token: "", gistId: sync.gistId, last: "" }; save(SYNC_KEY, sync); renderSettings(); toast("Sync off (token forgotten)"); };

  // ---------- boot ----------
  function relTime(iso) { return iso ? "Updated " + ago(iso) : "No data yet"; }

  async function boot() {
    applyTheme(); bindFilters(); updateBadge();
    try {
      const r = await fetch("jobs.json", { cache: "no-cache" });
      data = await r.json();
    } catch {
      toast("Couldn't load jobs (offline?)");
    }
    data.jobs = data.jobs || [];
    $("#updated").textContent = relTime(data.generated_at);
    const srcs = [...new Set(data.jobs.flatMap(j => j.sources || [j.source]))].sort();
    for (const s of srcs) $("#source").append(el("option", { value: s }, s));
    $("#source").value = srcs.includes(prefs.source) ? prefs.source : "";
    renderJobs();
    // Mark this visit so next time "NEW" means new since now (stored after first render).
    save(SEEN_KEY, now());
    if (sync.token) doSync(false);
  }

  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
  window.__jobseeker = { mergeInto, get store() { return store; } }; // for tests/debugging
  boot();
})();
