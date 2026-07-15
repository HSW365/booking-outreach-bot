"""
hsw365_offer_lead_finder.py — finds local business leads (auto repair,
salons, contractors, restaurants, dentists, etc.) around South Jersey /
Philadelphia for the HSW365 Front Desk + Website offer campaign, and
attaches a contact email where one can be found on their existing site.

Uses OpenStreetMap's Overpass API — completely free, no API key, no
billing account required. (Originally used Google Places API (New), but
that requires an active Google Cloud billing account even for free-tier
usage, which isn't available right now — Overpass needs nothing.)

Coverage/tradeoffs vs Google Places: OSM data is community-maintained, so
some small businesses are missing or have stale info, and phone/website
tags are filled in less consistently than Google's. It's still a solid,
genuinely free source for this — and the email step only needs the
`website` tag to be present, same as before.

Usage:
    python hsw365_offer_lead_finder.py
"""

import json
import os
import re
import time

import requests

import config

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Business category -> OSM tag(s) that best represent it. Categories with
# no reliable OSM equivalent (e.g. "cleaning service") are left out rather
# than guessing with unreliable tags.
CATEGORY_TAGS = {
    "auto repair shop": [("shop", "car_repair")],
    "hair salon": [("shop", "hairdresser")],
    "nail salon": [("shop", "beauty")],
    "restaurant": [("amenity", "restaurant")],
    "plumber": [("craft", "plumber")],
    "electrician": [("craft", "electrician")],
    "landscaping company": [("craft", "gardener")],
    "dentist": [("amenity", "dentist")],
    "real estate agent": [("office", "estate_agent")],
    "law office": [("office", "lawyer")],
    "insurance agency": [("office", "insurance")],
    "tax preparer": [("office", "tax_advisor")],
    "daycare center": [("amenity", "childcare")],
}

DEBUG_FILE = os.path.join(
    os.environ.get("OFFER_DATA_DIR", os.path.join(os.path.dirname(__file__), "data")),
    "hsw365_offer_debug.json",
)
_debug_entries = []


def _log_debug(query, status_code, body_snippet):
    _debug_entries.append({
        "query": query,
        "status_code": status_code,
        "response_snippet": body_snippet[:300],
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def _flush_debug():
    os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)
    with open(DEBUG_FILE, "w") as f:
        json.dump(_debug_entries, f, indent=2)


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def search_overpass(category, tag_pairs):
    """One Overpass QL call for a category. Returns list of element dicts."""
    clauses = []
    for key, value in tag_pairs:
        for kind in ("node", "way"):
            clauses.append(
                f'{kind}["{key}"="{value}"](around:{config.SEARCH_RADIUS_METERS},'
                f'{config.SEARCH_LAT},{config.SEARCH_LNG});'
            )
    ql = f"[out:json][timeout:30];\n(\n  " + "\n  ".join(clauses) + "\n);\nout center tags;"

    resp = requests.post(
        OVERPASS_URL,
        data={"data": ql},
        headers={"User-Agent": "HSW365Media-LeadFinder/1.0 (hsw365media@gmail.com)"},
        timeout=45,
    )
    _log_debug(category, resp.status_code, resp.text)
    if resp.status_code != 200:
        print(f"[offer_lead_finder]   Overpass error {resp.status_code}: {resp.text[:300]}")
        return []
    return resp.json().get("elements", [])


def find_email_on_site(website):
    """Try a handful of common contact page paths, return first email found."""
    if not website:
        return None
    if not website.startswith("http"):
        website = "https://" + website
    base = website.rstrip("/")
    for path in config.CONTACT_PATH_CANDIDATES:
        url = f"{base}/{path}".rstrip("/")
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                match = EMAIL_RE.search(r.text)
                if match:
                    email = match.group(0)
                    if not email.lower().endswith((".png", ".jpg", ".gif")):
                        return email
        except requests.RequestException:
            continue
        time.sleep(0.5)
    return None


def _format_address(tags):
    parts = [tags.get("addr:housenumber"), tags.get("addr:street")]
    line1 = " ".join(p for p in parts if p)
    city_state = ", ".join(p for p in (tags.get("addr:city"), tags.get("addr:state")) if p)
    return ", ".join(p for p in (line1, city_state) if p) or None


def run():
    leads = _load_json(config.OFFER_LEADS_FILE, [])
    known_ids = {lead["place_id"] for lead in leads if lead.get("place_id")}

    new_count = 0
    for category, tag_pairs in CATEGORY_TAGS.items():
        print(f"[offer_lead_finder] searching: {category}")
        try:
            elements = search_overpass(category, tag_pairs)
        except Exception as e:
            print(f"[offer_lead_finder] search failed for '{category}': {e}")
            continue

        print(f"[offer_lead_finder]   {len(elements)} results returned")

        for el in elements:
            osm_id = f"{el.get('type')}/{el.get('id')}"
            tags = el.get("tags", {})
            name = tags.get("name")
            if not osm_id or not name or osm_id in known_ids:
                continue

            website = tags.get("website") or tags.get("contact:website")
            phone = tags.get("phone") or tags.get("contact:phone")
            email = find_email_on_site(website) if website else None

            lead = {
                "place_id": osm_id,
                "name": name,
                "address": _format_address(tags),
                "phone": phone,
                "website": website,
                "email": email,
                "source_query": category,
                "status": "found",
                "found_at": time.strftime("%Y-%m-%d"),
                "last_contacted": None,
                "touches_sent": 0,
            }
            leads.append(lead)
            known_ids.add(osm_id)
            new_count += 1
            print(f"[offer_lead_finder]   + {name} — email: {email or 'NOT FOUND'}")

        time.sleep(1)  # be polite to the free public Overpass instance

    _save_json(config.OFFER_LEADS_FILE, leads)
    _flush_debug()
    print(f"[offer_lead_finder] done. {new_count} new leads added. {len(leads)} total in file.")


if __name__ == "__main__":
    run()
