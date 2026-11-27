"""
booking_lead_finder.py — finds potential booking leads (schools, colleges,
veteran orgs, libraries, community centers, chambers of commerce) around
South Jersey / Philadelphia and attaches a contact email where possible.

Uses the Places API (New) — Text Search endpoint.
Requires: GOOGLE_PLACES_API_KEY (with "Places API (New)" enabled)

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

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.websiteUri,places.nationalPhoneNumber"
)


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
    """One Places API (New) Text Search call. Returns list of place dicts."""
    if not config.GOOGLE_PLACES_API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": config.SEARCH_LAT,
                    "longitude": config.SEARCH_LNG,
                },
                "radius": float(config.SEARCH_RADIUS_METERS),
            }
        },
    }
    resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=15)
    if resp.status_code != 200:
        print(f"[lead_finder]   API error {resp.status_code}: {resp.text[:300]}")
        return []
    return resp.json().get("places", [])


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
                    if not email.lower().endswith((".png", ".jpg", ".gif")):
                        return email
        except requests.RequestException:
            continue
        time.sleep(0.5)
    return None


def free_leads():
    """Free fallback (OpenStreetMap, no key): organizations within range that publish an email."""
    near = f"(around:{config.SEARCH_RADIUS_METERS},{config.SEARCH_LAT},{config.SEARCH_LNG})"
    kinds = '["amenity"~"^(school|college|university|library|community_centre|theatre|arts_centre|events_venue)$"]'
    parts = "".join(f'nwr{near}{k}["{e}"];' for k in (kinds, '["club"~"^(veterans|youth)$"]')
                    for e in ("email", "contact:email"))
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                "https://overpass.private.coffee/api/interpreter"):
        try:
            r = requests.post(url, data={"data": f"[out:json][timeout:120];({parts});out tags;"}, timeout=150,
                              headers={"User-Agent": "HSW365-Booking/1.0 (hsw365media@gmail.com)"})
            if r.status_code == 200:
                return r.json().get("elements", [])
            print(f"[lead_finder]   {url} -> {r.status_code}")
        except (requests.RequestException, ValueError) as e:
            print(f"[lead_finder]   {url} failed: {e}")
    return []


def add_free_leads(leads):
    known = {(l.get("email") or "").lower() for l in leads}
    added = 0
    for el in free_leads():
        t = el.get("tags", {})
        email = (t.get("email") or t.get("contact:email") or "").split(";")[0].strip().lower()
        name = t.get("name")
        if not name or not EMAIL_RE.fullmatch(email) or email in known or email.endswith((".png", ".jpg", ".webp")):
            continue
        known.add(email)
        leads.append({
            "place_id": f"osm-{el.get('type')}-{el.get('id')}", "name": name,
            "address": ", ".join(x for x in (t.get("addr:city"), t.get("addr:state")) if x) or None,
            "phone": t.get("phone"), "website": t.get("website"), "email": email,
            "source_query": f"openstreetmap {t.get('amenity') or t.get('club')}", "status": "found",
            "found_at": time.strftime("%Y-%m-%d"), "last_contacted": None, "followups_sent": 0,
        })
        added += 1
    return added


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

        print(f"[lead_finder]   {len(results)} results returned")

        for place in results:
            place_id = place.get("id")
            if not place_id or place_id in known_place_ids:
                continue

            website = place.get("websiteUri")
            email = find_email_on_site(website) if website else None
            name = (place.get("displayName") or {}).get("text", "Unknown")

            lead = {
                "place_id": place_id,
                "name": name,
                "address": place.get("formattedAddress"),
                "phone": place.get("nationalPhoneNumber"),
                "website": website,
                "email": email,
                "source_query": query,
                "status": "found",
                "found_at": time.strftime("%Y-%m-%d"),
                "last_contacted": None,
                "followups_sent": 0,
            }
            leads.append(lead)
            known_place_ids.add(place_id)
            new_count += 1
            print(f"[lead_finder]   + {name} — email: {email or 'NOT FOUND'}")

    if not new_count:
        new_count = add_free_leads(leads)

    _save_json(config.LEADS_FILE, leads)
    print(f"[lead_finder] done. {new_count} new leads added. {len(leads)} total in file.")


if __name__ == "__main__":
    run()
