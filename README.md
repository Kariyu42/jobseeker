# jobseeker

A personal job finder for **remote DevOps / SRE / Platform / Cloud** roles that you can actually be hired for, with an application tracker. It works on **phone and laptop**, and it's **100% free**: no servers, no paid APIs, no accounts besides GitHub.

- 🔎 Pulls jobs every 6 hours from RemoteOK, Remotive, Arbeitnow, Himalayas, Jobicy, We Work Remotely, Working Nomads and Hacker News "Who is hiring".
- ✅ ⚠️ ❌ **Can they hire you?** Each job is checked against where you live, where you can work and your hours. That includes hidden "US-only" clauses in the description, the #1 reason remote applications get ignored.
- 🎯 **Match score** (0–100) from your skills, title fit, seniority and freshness.
- 📋 **Tracker**: Saved → Applied → Interview → Offer / Rejected, with notes and ⏰ follow-up reminders after 7 days.
- 📱 Installable app (PWA) that works offline. Sync between phone and laptop with export/import, or free auto-sync through a private GitHub Gist.
- 📘 [GUIDE.md](GUIDE.md): the strategy for why remote applications get no reply and what to do about it.

## How it works

```
GitHub Actions (free, every 6h)                GitHub Pages (free)
  fetcher/  ── fetch 8 boards                    docs/  ── the app
            ── keep DevOps titles      ──►            reads docs/jobs.json
            ── classify location                      tracker in your browser
            ── score + dedupe                         (+ optional Gist sync)
            ── write docs/jobs.json
```

## Setup (about 5 minutes)

1. **Merge into the default branch (`master`).** Scheduled workflows only run there. The workflow already has permission to commit (`permissions: contents: write`).
2. **Make the repo public:** Settings → General → Danger Zone → Change visibility. On GitHub Free, Pages only works for public repos, and Actions minutes are unlimited there. The repo only contains public job listings and your skill keywords: **don't put your CV, email or phone number in it.**
3. **Turn on Pages:** Settings → Pages → Source *Deploy from a branch* → Branch `master`, folder `/docs` → Save.
4. **First fetch:** Actions tab → **Fetch jobs** → *Run workflow*. After about a minute, open `https://<your-username>.github.io/jobseeker/`.
5. **On your phone**, open that URL:
   - iPhone: Safari → Share → *Add to Home Screen*
   - Android: Chrome menu → *Install app*

## Personalise

Edit **[`config.yml`](config.yml)**. You can do it right in the GitHub web editor, even from your phone. Committing it triggers a new fetch automatically. The settings are:

- `me`: home country, work authorization (`EU` expands to all EU/EEA countries), countries you'd live in, timezone range, level
- `skills`: your stack with weights. Make it match your CV.
- `title_include` / `title_exclude`: which job titles count
- `max_age_days`, `min_salary`

## Sync phone ⇄ laptop

Your tracker lives in each browser. There are two free options:

- **Export / Import** (Settings tab): download a file on one device, import it on the other.
- **Auto-sync via a private Gist:**
  1. Create a *fine-grained* token with only **Gists: read & write** (GitHub → Settings → Developer settings → Personal access tokens).
  2. Paste it in Settings → *Sync now*.
  3. Copy the Gist ID it creates to your other device, together with the same token.

  After that, every change syncs automatically.

## Run locally

```bash
pip install -r requirements.txt
python -m pytest -q                         # tests
python -m fetcher.main                      # fetch → docs/jobs.json
python -m fetcher.main --only remotive,himalayas
python -m http.server -d docs 8000          # open http://localhost:8000
```

## Adding a job board

Add `fetcher/sources/<name>.py` with `fetch(http) -> list[dict]`. Build each job with `normalize.job(...)`, then register the module in `fetcher/sources/__init__.py`. If a board fails, it's logged and skipped, so it never breaks a run.

## Notes

- GitHub pauses scheduled workflows in repos with **no activity for 60 days**. The bot's commits usually keep it alive. If it ever stops, click *Enable workflow* in the Actions tab.
- Classification is heuristic. ⚠️ means "read the posting": many of those are fine.
