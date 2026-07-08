# HSW365 Booking Outreach Bot

Autonomous bot that finds potential booking clients (schools, colleges,
veteran orgs, libraries, community centers, chambers of commerce) around
South Jersey / Philadelphia, and emails them a personalized pitch to book
**Elvin "Ali" Torres Sr.** to present the **HSW365 Live Experience**
(Army veteran story, Respect Da Game Podcast, published author, recording
artist, app developer, HOODSTARWORLD streetwear founder).

Runs daily on GitHub Actions, same pattern as your QUEENEE lead-gen and
GTA6HQ pipelines. It never sends more than `MAX_EMAILS_PER_RUN` in one run
(default 8) to stay well under spam-filter radar and give you time to react
to replies.

## What it does each run

1. **`booking_lead_finder.py`** — searches Google Places for organizations
   that book speakers (schools, colleges, veteran orgs, libraries, chambers
   of commerce) within ~50 miles of Vineland, NJ, and scrapes their website
   for a contact email. New leads get appended to `data/leads.json`.
2. **`email_composer.py`** — generates a personalized pitch email per lead
   using the Anthropic API (falls back to a solid static template if no key
   is set), pulling 2-3 relevant pillars from your bio and the right fee
   tier ($3,500–$10,000 depending on org type — from your existing EPK).
3. **`outreach_sender.py`** — sends the email via SendGrid or Gmail SMTP.
4. **`main.py`** — orchestrates all of the above, plus sends a single
   automatic follow-up after 7 days (configurable) if there's been no
   status change, capped at 2 follow-ups per lead.
5. Everything is logged to `data/contacted_log.json` and lead status is
   tracked in `data/leads.json` (`found` → `emailed` → `replied`/`booked`/`dead`).

**This bot never reads your inbox.** Replies go straight to
`book@hoodstar365.com` like normal — you or whoever checks that inbox
updates the lead status manually with `tracker.py` so the bot knows to stop
following up.

## Setup

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Environment variables

| Variable | Required | Notes |
|---|---|---|
| `GOOGLE_PLACES_API_KEY` | Yes, for auto lead-finding | You already use this for `queenee_lead_finder.py` — same key works here. |
| `ANTHROPIC_API_KEY` | Recommended | Personalizes each email. Without it, a solid static template is used instead. |
| `SEND_PROVIDER` | No | `smtp` (default — go-live path) or `sendgrid` (switch later once that key is ready) |
| `SMTP_USER` | Yes (default path) | `hsw365media@gmail.com` |
| `SMTP_PASSWORD` | Yes (default path) | A Gmail **App Password**, not your real Gmail password — see steps below. |
| `SENDGRID_API_KEY` | Only if `SEND_PROVIDER=sendgrid` | Real key looks like `SG.xxxxx...`, from SendGrid dashboard → Settings → API Keys. Not your Twilio token, not a docs snippet. |
| `FROM_EMAIL` | No | Defaults to `book@hoodstar365.com` |
| `MAX_EMAILS_PER_RUN` | No | Default 8 |
| `FOLLOWUP_AFTER_DAYS` | No | Default 7 |

### Getting a Gmail App Password (2 minutes, this is the go-live path)

1. Go to myaccount.google.com → Security → make sure **2-Step Verification** is ON for `hsw365media@gmail.com` (required for app passwords to exist as an option).
2. Go directly to **myaccount.google.com/apppasswords**.
3. Name it something like `hsw365-booking-bot`, click Create.
4. Google shows you a 16-character password **once** — that's your `SMTP_PASSWORD`. `SMTP_USER` is just `hsw365media@gmail.com`.
5. Put both straight into GitHub Secrets (or wherever you're running this) — never paste them into chat.

### 3. Run once locally to test

```bash
python main.py
```

### 4. Check pipeline status any time

```bash
python tracker.py summary
python tracker.py set "Example Community College" booked
```

### 5. Deploy on GitHub Actions (recommended — fully autonomous)

1. Push this folder to a new repo, e.g. `HSW365/booking-outreach-bot`.
2. In repo Settings → Secrets and variables → Actions, add:
   `GOOGLE_PLACES_API_KEY`, `ANTHROPIC_API_KEY`, `SEND_PROVIDER`,
   `SENDGRID_API_KEY` (or `SMTP_USER`/`SMTP_PASSWORD`), `FROM_EMAIL`.
3. The workflow in `.github/workflows/daily-booking-outreach.yml` runs
   daily at 9am ET and commits updated lead/log data back to the repo —
   so your pipeline state lives in git, same as your other automations.
4. Trigger a manual test run anytime from the Actions tab
   ("Run workflow" button).

## Which sender should I use?

- **SendGrid** — cleanest for volume/deliverability, matches the infra
  you're already setting up for QUEENEE. Needs `SENDGRID_API_KEY` and a
  verified sender identity for `book@hoodstar365.com` (or whatever
  `FROM_EMAIL` you use) in SendGrid.
- **Gmail SMTP** — simplest to stand up right now since
  `hsw365media@gmail.com` is already your working account, but Gmail caps
  sends per day (~500) and is more likely to get flagged if volume grows.
  Fine at 8 emails/day.

## Notes / things to know

- Emails found by scraping public "contact"/"about"/"staff" pages aren't
  always accurate — leads with no email found are logged with
  `status: "found"` and `email: null` so you can add one by hand in
  `data/leads.json` instead of the bot guessing.
- The default fee framing pulled from your existing EPK: schools/nonprofits
  $3,500–$5,000, colleges/community orgs $5,000–$7,500, corporate/conference
  $7,500–$10,000. Edit these in `config.py` (`FEE_TIERS`) any time.
- Edit the six pillars (veteran/speaker, podcast, author, artist, app
  developer, streetwear founder) directly in `config.py` (`PILLARS`) if your
  bio or accolades change.
- To pause outreach entirely without deleting anything, just disable the
  GitHub Actions workflow.
