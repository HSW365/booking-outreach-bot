"""
booking_lead_finder.py — finds potential booking leads (schools, colleges,
veteran orgs, libraries, community centers, chambers of commerce) around
South Jersey / Philadelphia and attaches a scraped contact email where
possible.

Requires: GOOGLE_PLACES_API_KEY

Usage:
    python booking_lead_finder.py
"""

import json
import os
import re
import time

import requests

import config

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

PLACES_TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def search_places(query):
    """One Google Places Text Search call. Returns list of place dicts."""
    if not config.GOOGLE_PLACES_API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set")

    params = {
        "query": query,
        "location": f"{config.SEARCH_LAT},{config.SEARCH_LNG}",
        "radius": config.SEARCH_RADIUS_METERS,
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    resp = requests.get(PLACES_TEXTSEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_place_website(place_id):
    params = {
        "place_id": place_id,
        "fields": "name,website,formatted_phone_number,formatted_address",
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("result", {})


def find_email_on_site(website):
    """Try a handful of common contact page paths, return first email found."""
    if not website:
        return None
    base = website.rstrip("/")
    for path in config.CONTACT_PATH_CANDIDATES:
        url = f"{base}/{path}".rstrip("/")
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                match = EMAIL_RE.search(r.text)
                if match:
                    email = match.group(0)
                    # filter obvious junk (image files misread as emails, etc.)
                    if not email.lower().endswith((".png", ".jpg", ".gif")):
                        return email
        except requests.RequestException:
            continue
        time.sleep(0.5)
    return None


def run():
    leads = _load_json(config.LEADS_FILE, [])
    known_place_ids = {lead["place_id"] for lead in leads if lead.get("place_id")}

    new_count = 0
    for query in config.LEAD_SEARCH_QUERIES:
        print(f"[lead_finder] searching: {query}")
        try:
            results = search_places(query)
        except Exception as e:
            print(f"[lead_finder] search failed for '{query}': {e}")
            continue

        for place in results:
            place_id = place.get("place_id")
            if not place_id or place_id in known_place_ids:
                continue

            details = get_place_website(place_id)
            website = details.get("website")
            email = find_email_on_site(website) if website else None

            lead = {
                "place_id": place_id,
                "name": details.get("name") or place.get("name"),
                "address": details.get("formatted_address") or place.get("formatted_address"),
                "phone": details.get("formatted_phone_number"),
                "website": website,
                "email": email,
                "source_query": query,
                "status": "found",       # found -> emailed -> followup_1 -> followup_2 -> replied/booked/dead
                "found_at": time.strftime("%Y-%m-%d"),
                "last_contacted": None,
                "followups_sent": 0,
            }
            leads.append(lead)
            known_place_ids.add(place_id)
            new_count += 1
            print(f"[lead_finder]   + {lead['name']} — email: {email or 'NOT FOUND'}")

    _save_json(config.LEADS_FILE, leads)
    print(f"[lead_finder] done. {new_count} new leads added. {len(leads)} total in file.")


if __name__ == "__main__":
    run()
