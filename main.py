"""
main.py — the autonomous booking outreach run.

Each run:
  1. Pulls in any brand-new leads (calls booking_lead_finder).
  2. Sends first-touch emails to leads with status "found" and a known email
     (capped at MAX_EMAILS_PER_RUN).
  3. Sends follow-up emails to leads that were emailed >= FOLLOWUP_AFTER_DAYS
     ago and haven't replied/booked (up to MAX_FOLLOWUPS).
  4. Logs everything to data/contacted_log.json.

Intended to run on a schedule (see .github/workflows/daily-booking-outreach.yml).
Nothing here marks a lead "replied" or "booked" automatically — that's a
manual status update (see tracker.py) once Elvin/the booking inbox gets a
response, since this bot has no inbox-reading access by design.
"""

import datetime
import json
import os

import booking_lead_finder
import config
import email_composer
import outreach_sender


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _append_log(entry):
    log = _load_json(config.LOG_FILE, [])
    log.append(entry)
    _save_json(config.LOG_FILE, log)


def _days_since(date_str):
    then = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return (datetime.date.today() - then).days


def _send_first_touch(leads, sent_count):
    for lead in leads:
        if sent_count >= config.MAX_EMAILS_PER_RUN:
            break
        if lead.get("status") != "found":
            continue
        if not lead.get("email"):
            continue  # no contact email found — needs manual follow-up

        subject, body = email_composer.compose_email(lead)
        try:
            outreach_sender.send_email(lead["email"], subject, body)
            lead["status"] = "emailed"
            lead["last_contacted"] = datetime.date.today().isoformat()
            _append_log({
                "type": "first_touch",
                "lead": lead["name"],
                "email": lead["email"],
                "date": lead["last_contacted"],
                "subject": subject,
            })
            print(f"[main]   sent first-touch to {lead['name']} <{lead['email']}>")
            sent_count += 1
        except Exception as e:
            print(f"[main]   FAILED to send to {lead['name']}: {e}")
    return sent_count


def _send_followups(leads, sent_count):
    for lead in leads:
        if sent_count >= config.MAX_EMAILS_PER_RUN:
            break
        if lead.get("status") != "emailed":
            continue
        if lead.get("followups_sent", 0) >= config.MAX_FOLLOWUPS:
            continue
        if not lead.get("last_contacted"):
            continue
        if _days_since(lead["last_contacted"]) < config.FOLLOWUP_AFTER_DAYS:
            continue

        subject, body = email_composer.compose_email(lead)
        followup_body = (
            f"Following up on the note below in case it got buried — still "
            f"happy to find a date that works.\n\n---\n\n{body}"
        )
        try:
            outreach_sender.send_email(lead["email"], f"Re: {subject}", followup_body)
            lead["followups_sent"] = lead.get("followups_sent", 0) + 1
            lead["last_contacted"] = datetime.date.today().isoformat()
            _append_log({
                "type": "followup",
                "lead": lead["name"],
                "email": lead["email"],
                "date": lead["last_contacted"],
                "followup_number": lead["followups_sent"],
            })
            print(f"[main]   sent follow-up #{lead['followups_sent']} to {lead['name']}")
            sent_count += 1
        except Exception as e:
            print(f"[main]   FAILED follow-up to {lead['name']}: {e}")
    return sent_count


def run():
    print("=== HSW365 Booking Outreach Bot ===")
    print(f"Run date: {datetime.date.today().isoformat()}")

    if config.GOOGLE_PLACES_API_KEY:
        booking_lead_finder.run()
    else:
        print("[main] GOOGLE_PLACES_API_KEY not set — skipping lead discovery, "
              "working off existing data/leads.json only.")

    leads = _load_json(config.LEADS_FILE, [])
    if not leads:
        print("[main] no leads on file. Nothing to send.")
        return

    sent_count = 0
    sent_count = _send_first_touch(leads, sent_count)
    sent_count = _send_followups(leads, sent_count)

    _save_json(config.LEADS_FILE, leads)

    no_email = sum(1 for l in leads if l.get("status") == "found" and not l.get("email"))
    print(f"[main] run complete. {sent_count} emails sent this run.")
    if no_email:
        print(f"[main] {no_email} leads found with NO email on record — "
              f"review data/leads.json and add manually where possible.")


if __name__ == "__main__":
    run()
