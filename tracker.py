"""
tracker.py — manual status updates and a quick pipeline summary.

Since this bot deliberately has no inbox-reading access (booking replies
should go to a human), use this to record outcomes as they happen and see
where every lead stands.

Usage:
    python tracker.py summary
    python tracker.py set "Example Community College" replied
    python tracker.py set "Example Community College" booked
    python tracker.py set "Example Community College" dead

    # Same commands against the HSW365 Front Desk + Website offer campaign
    # instead of the default speaker-booking campaign:
    python tracker.py summary --offer
    python tracker.py set "Example Auto Repair" replied --offer
"""

import json
import sys

import config


def _leads_file(offer):
    return config.OFFER_LEADS_FILE if offer else config.LEADS_FILE


def _load(offer):
    with open(_leads_file(offer), "r") as f:
        return json.load(f)


def _save(leads, offer):
    with open(_leads_file(offer), "w") as f:
        json.dump(leads, f, indent=2)


def summary(offer=False):
    leads = _load(offer)
    counts = {}
    for lead in leads:
        counts[lead.get("status", "unknown")] = counts.get(lead.get("status", "unknown"), 0) + 1

    label = "HSW365 Offer" if offer else "Booking"
    print(f"=== {label} Pipeline Summary ===")
    for status in ["found", "emailed", "replied", "booked", "dead"]:
        print(f"  {status:10s}: {counts.get(status, 0)}")
    print(f"  {'TOTAL':10s}: {len(leads)}")

    booked = [l for l in leads if l.get("status") == "booked"]
    if booked:
        print("\nBooked/closed:")
        for l in booked:
            print(f"  - {l['name']}")

    replied = [l for l in leads if l.get("status") == "replied"]
    if replied:
        print("\nAwaiting your response:")
        for l in replied:
            print(f"  - {l['name']} <{l.get('email')}>")


def set_status(name_fragment, new_status, offer=False):
    valid = {"found", "emailed", "replied", "booked", "dead", "do_not_contact"}
    if new_status not in valid:
        print(f"Invalid status '{new_status}'. Must be one of: {sorted(valid)}")
        return

    leads = _load(offer)
    matches = [l for l in leads if name_fragment.lower() in (l.get("name") or "").lower()]

    if not matches:
        print(f"No lead matching '{name_fragment}' found.")
        return
    if len(matches) > 1:
        print("Multiple matches, be more specific:")
        for l in matches:
            print(f"  - {l['name']}")
        return

    matches[0]["status"] = new_status
    _save(leads, offer)
    print(f"Updated '{matches[0]['name']}' -> {new_status}")


if __name__ == "__main__":
    args = sys.argv[1:]
    offer_flag = "--offer" in args
    if offer_flag:
        args.remove("--offer")

    if len(args) < 1:
        print(__doc__)
    elif args[0] == "summary":
        summary(offer=offer_flag)
    elif args[0] == "set" and len(args) == 3:
        set_status(args[1], args[2], offer=offer_flag)
    else:
        print(__doc__)
