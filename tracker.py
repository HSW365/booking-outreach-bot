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
"""

import json
import sys

import config


def _load():
    with open(config.LEADS_FILE, "r") as f:
        return json.load(f)


def _save(leads):
    with open(config.LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def summary():
    leads = _load()
    counts = {}
    for lead in leads:
        counts[lead.get("status", "unknown")] = counts.get(lead.get("status", "unknown"), 0) + 1

    print("=== Booking Pipeline Summary ===")
    for status in ["found", "emailed", "replied", "booked", "dead"]:
        print(f"  {status:10s}: {counts.get(status, 0)}")
    print(f"  {'TOTAL':10s}: {len(leads)}")

    booked = [l for l in leads if l.get("status") == "booked"]
    if booked:
        print("\nBooked:")
        for l in booked:
            print(f"  - {l['name']}")

    replied = [l for l in leads if l.get("status") == "replied"]
    if replied:
        print("\nAwaiting your response:")
        for l in replied:
            print(f"  - {l['name']} <{l.get('email')}>")


def set_status(name_fragment, new_status):
    valid = {"found", "emailed", "replied", "booked", "dead"}
    if new_status not in valid:
        print(f"Invalid status '{new_status}'. Must be one of: {sorted(valid)}")
        return

    leads = _load()
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
    _save(leads)
    print(f"Updated '{matches[0]['name']}' -> {new_status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    elif sys.argv[1] == "summary":
        summary()
    elif sys.argv[1] == "set" and len(sys.argv) == 4:
        set_status(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
