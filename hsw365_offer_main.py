"""
hsw365_offer_main.py — the autonomous HSW365 Front Desk + Website offer run.

Separate campaign from main.py (speaker booking). Each run:
  1. Pulls in any brand-new local-business leads (calls hsw365_offer_lead_finder).
  2. Sends touch 1 to leads with status "found" and a known email.
  3. Sends touch 2 to leads emailed >= OFFER_TOUCH2_AFTER_DAYS ago with 1 touch sent.
  4. Sends touch 3 to leads emailed >= OFFER_TOUCH3_AFTER_DAYS ago with 2 touches sent.
  5. Logs everything to data/hsw365_offer_contacted_log.json.

Nothing here marks a lead "replied"/"booked" automatically — same manual
workflow as the booking bot (tracker.py) once a reply comes in to
hsw365media@gmail.com / book@hoodstar365.com.

Intended to run on a schedule (see .github/workflows/hsw365-offer.yml).
"""

import datetime
import json
import os

import config
import hsw365_offer_composer as composer
import hsw365_offer_lead_finder
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
    log = _load_json(config.OFFER_LOG_FILE, [])
    log.append(entry)
    _save_json(config.OFFER_LOG_FILE, log)


def _days_since(date_str):
    then = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return (datetime.date.today() - then).days


def _send_touch(lead, touch_number):
    subject, body = composer.TOUCH_COMPOSERS[touch_number](lead)
    outreach_sender.send_email(
        lead["email"], subject, body,
        from_name=config.OFFER_FROM_NAME, reply_to=config.OFFER_REPLY_TO,
    )
    lead["status"] = "emailed"
    lead["touches_sent"] = touch_number
    lead["last_contacted"] = datetime.date.today().isoformat()
    _append_log({
        "type": f"touch_{touch_number}",
        "lead": lead["name"],
        "email": lead["email"],
        "date": lead["last_contacted"],
        "subject": subject,
    })
    print(f"[offer_main]   sent touch {touch_number} to {lead['name']} <{lead['email']}>")


def _run_sequence(leads, sent_count):
    for lead in leads:
        if sent_count >= config.OFFER_MAX_EMAILS_PER_RUN:
            break
        if not lead.get("email"):
            continue  # no contact email found — better fit for the CallTwin calling agent
        if lead.get("status") in ("replied", "booked", "dead", "do_not_contact"):
            continue

        touches_sent = lead.get("touches_sent", 0)

        try:
            if touches_sent == 0:
                _send_touch(lead, 1)
                sent_count += 1
            elif touches_sent == 1 and lead.get("last_contacted") and \
                    _days_since(lead["last_contacted"]) >= config.OFFER_TOUCH2_AFTER_DAYS:
                _send_touch(lead, 2)
                sent_count += 1
            elif touches_sent == 2 and lead.get("last_contacted") and \
                    _days_since(lead["last_contacted"]) >= config.OFFER_TOUCH3_AFTER_DAYS:
                _send_touch(lead, 3)
                sent_count += 1
            # touches_sent == 3 -> sequence complete, no further action.
        except Exception as e:
            _append_log({
                "type": "send_error",
                "lead": lead["name"],
                "email": lead.get("email"),
                "error": str(e),
                "date": datetime.date.today().isoformat(),
            })
            print(f"[offer_main]   FAILED touch for {lead['name']}: {e}")

    return sent_count


def run():
    print("=== HSW365 Front Desk + Website Offer Bot ===")
    print(f"Run date: {datetime.date.today().isoformat()}")
    print(f"[offer_main] SEND_PROVIDER = {config.SEND_PROVIDER}")
    print(f"[offer_main] lead source = OpenStreetMap Overpass (free, no key needed)")
    print(f"[offer_main] SMTP_USER set: {bool(config.SMTP_USER)}")

    hsw365_offer_lead_finder.run()

    leads = _load_json(config.OFFER_LEADS_FILE, [])
    _save_json(config.OFFER_LEADS_FILE, leads)  # ensure the file exists even if empty
    _save_json(config.OFFER_LOG_FILE, _load_json(config.OFFER_LOG_FILE, []))  # same for the log

    if not leads:
        print("[offer_main] no leads on file. Nothing to send.")
        return

    sent_count = _run_sequence(leads, 0)
    _save_json(config.OFFER_LEADS_FILE, leads)

    no_email = sum(1 for l in leads if not l.get("email") and l.get("status") == "found")
    print(f"[offer_main] run complete. {sent_count} emails sent this run.")
    if no_email:
        print(f"[offer_main] {no_email} leads found with NO email on record — "
              f"these are better targets for the CallTwin calling+SMS agent instead.")


if __name__ == "__main__":
    run()
