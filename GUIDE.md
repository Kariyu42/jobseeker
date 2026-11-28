# Getting hired remotely as a DevOps engineer: the playbook

You're applying to "100% remote" jobs and hearing nothing back. That usually isn't about your skills. It's a targeting problem. This guide explains why it happens and what to do instead.

---

## 1. Why "remote" applications get silently dropped

1. **"Remote" rarely means "anywhere".** Most remote postings on the big boards are *remote inside one country*, usually the US, because of payroll, tax and labour law. An ATS (applicant tracking system) often auto-rejects anyone whose location doesn't match. Nobody ever reads the application.
2. **"Worldwide" roles get flooded.** A truly worldwide DevOps post can get 500–2,000 applicants in its first 48 hours. If you apply on day 5, it's mostly already decided.
3. **Generic CVs lose to keyword filters.** If the posting says "Terraform, EKS, ArgoCD" and your CV says "infrastructure automation", the ATS and the recruiter's 8-second skim will both miss you.
4. **Timezone overlap matters more than the label.** "Remote (US)" frequently really means "you must overlap with 9–5 Eastern".

**What the app does about this:** every job gets a ✅ / ⚠️ / ❌ badge based on where you live, where you can legally work and your hours. It reads the description too, catching phrases like "must be authorized to work in the US", "401k" or "security clearance". By default you only see ✅ jobs.

---

## 2. Where remote DevOps hiring that you can actually win happens

Ranked by response rate for someone based in the EU:

| Target | Why it works |
|---|---|
| **EU/EMEA-remote roles** (✅ in the app) | Smaller pool than worldwide, and you match their legal and timezone needs. Best ROI. |
| **European scale-ups and SaaS companies** (Berlin, Amsterdam, Paris, Lisbon, Barcelona, Stockholm) | Many hire "remote within EU" through local entities or an EOR. |
| **Companies that pay via Deel / Remote.com / Oyster** (contractor/EOR) | They've already solved hiring someone abroad, so your location is not a blocker. |
| **Freelance / B2B contracts** (Malt, Freelance.de, Toptal, Arc, Gun.io, direct) | DevOps contract work is common and often 100% remote. A good way in while you job-hunt. |
| **Hacker News "Who is hiring"** (included in the app) | Posts come straight from engineers and founders, not recruiters. Reply by email. |
| **Your own country, "remote-friendly"** | Easiest paperwork. Once you're inside the company, moving to another EU country is often just a conversation. |

---

## 3. The application routine (15 minutes per job, not 2)

1. **Apply within 48 hours of posting.** Sort by "Newest" and check "New only" daily. Freshness is part of the match score for this reason.
2. **Mirror their keywords.** Keep a master CV and spend 5 minutes swapping the top 3–4 bullets to the tools named in the posting. Use their exact words ("GitHub Actions", not "CI pipelines").
3. **Quantify.** "Cut deploy time from 40 to 6 min", "Moved 30 services to EKS with Terraform", "Cut AWS bill 28%". Numbers get read.
4. **First line of the cover note = proof, not intro.** For example: *"I run the Terraform + ArgoCD setup for a 40-service k8s platform, very close to what you describe."* Keep it to 3–5 sentences total.
5. **Say your location and hours up front.** *"Based in France (CET), work authorization across the EU, happy to overlap until 19:00 CET."* This removes the recruiter's main worry.
6. **Contact a human.** Find an engineer or engineering manager at the company (LinkedIn or GitHub) and send two lines: *"Applied for the Platform Engineer role, I've done X which seems close to your Y. Happy to share more."* This alone can double response rates.
7. **Follow up once after 7 days.** The tracker flags this for you (⏰).

---

## 4. Make your profile do the work

- **A public portfolio repo** is the strongest signal you can have for a remote DevOps role. One repo with:
  - Terraform for a small AWS/GCP setup (VPC, cluster, IAM)
  - a k8s app deployed via Helm/ArgoCD
  - a GitHub Actions pipeline (lint → test → build → deploy)
  - Prometheus/Grafana dashboards
  - a README with an architecture diagram and the "why" behind your choices

  Link it at the top of your CV.
- **Certifications that actually move the needle for remote roles:** CKA/CKAD, AWS SAA (or DevOps Pro), Terraform Associate. One is enough to get past filters.
- **LinkedIn:** headline like *"DevOps / Platform Engineer · Kubernetes · Terraform · AWS · Remote (EU)"*. Turn on "Open to work → Remote" and list several EU countries.

---

## 5. Living in other places while working

**What the badges on each job mean:**

| Badge | Meaning | What you do |
|---|---|---|
| ✅ *Open to people in France* / *Anywhere in Europe (incl. France)* / *Worldwide* | You can do the job from where you live now. | Apply. The company handles hiring you in France (French payroll, an Employer of Record, or a contractor setup). |
| 🧳 *Must live in Germany: you'd need to move* | The company only employs people who live in that country. As an EU citizen you're **allowed** to move there and work, with no visa. | Either move (tap the badge for that country's registration steps), or ask the recruiter if they can hire you in France via an EOR or as a contractor. |
| ❌ *Restricted to United Kingdom / United States…* | You'd need a visa, or the timezone doesn't fit. | Skip, unless they offer contractor/EOR hiring abroad. |

The app's **🌍 Countries** tab has the rules for each EU/EEA country, Switzerland, the UK, the US and Canada:
- right to work;
- what to register after moving, and the deadline;
- how a foreign company can employ you while you stay in France;
- links to official sources.

Some key facts:
- **As an EU citizen** you can live and work in any EU/EEA country plus Switzerland. In most of them you must register after arrival, usually within 3 months, but sometimes within days: Germany ~14 days, the Netherlands 5 days, Austria 3 days for the address.
  - Watch **tax residency**: you usually become tax-resident where you live and work. France keeps you as a French tax resident if your home or main stay (183+ days), main job or economic interests are in France.
  - If you move while keeping a remote job, tell your employer. Your social security moves with you, so they must be able to employ you in the new country.
- **Why "must live in X" happens:** if you work from France, French social security applies even for a foreign employer. That employer must then register in France (URSSAF CNFE) or use an EOR. Partial telework from France (25% to under 50%) can stay under the employer country's system under the 2023 EU framework agreement, but 100% remote can't.
- **Outside the EU** (UK, US, Canada, Georgia, the UAE…) you need a visa or work permit. Digital-nomad visas exist in several non-EU countries. Inside the EU you don't need them.
- **Contractor/B2B status** (e.g. French *auto-entrepreneur* or a SASU) gives the most freedom over where you live. Many EU startups prefer contractors for international hires.
- **Timezone:** staying within UTC-1 to UTC+4 keeps you eligible for nearly all EU roles. Set your range in `config.yml` (`timezone_min` / `timezone_max`).

---

## 6. Weekly rhythm

| When | What |
|---|---|
| Daily (10 min) | Open the app → "New only" → save anything ✅ with a score of 60 or more. |
| 3× a week | Send 3–5 tailored applications from Saved, each with one human contacted. |
| Weekly | Do the follow-ups flagged ⏰. Improve one thing in your portfolio repo. Adjust `config.yml` skills if you keep seeing a tool you don't list. |
| Monthly | Reply to the new HN "Who is hiring" posts in the first 2 days of the month. |

Aim for quality: 10 targeted applications a week, each to a ✅ job and each with a human contacted, beat 100 blind applications to "remote (US)" roles.
