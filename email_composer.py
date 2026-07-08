"""
email_composer.py — generates a personalized booking-pitch email for a given
lead using the Anthropic API. Falls back to a solid static template if no
ANTHROPIC_API_KEY is set, so the bot never blocks on this step.
"""

import json

import requests

import config

SYSTEM_PROMPT = f"""You write short, warm, professional booking-outreach emails on
behalf of a speakers bureau representing {config.SPEAKER_NAME}, an Army veteran,
motivational speaker, published author, recording artist, podcast host, app
developer, and streetwear brand founder.

Rules:
- 150-220 words max.
- One clear ask: would they like to book him to present the "{config.BRAND_NAME}"
  for their organization/audience.
- Reference the specific organization by name and, if you can infer it, why this
  audience specifically would value the talk (students, veterans, employees, etc).
- Weave in 2-3 of the pillars provided, not all of them — pick the ones most
  relevant to that organization.
- Include the fee range appropriate to the org type, framed as a starting point,
  not a hard number.
- End with a clear call to action to reply or book a call, and the booking email.
- No emojis. No exclamation-point stacking. Confident, not salesy.
- Output ONLY the email body text. No subject line, no preamble, no markdown."""


def _static_fallback(lead, fee_tier):
    pillars_text = "\n".join(f"- {name}: {desc}" for name, desc in config.PILLARS[:3])
    return f"""Hi {lead.get('name', 'there')} team,

I'm reaching out on behalf of {config.SPEAKER_NAME}, an Army veteran, published
author, recording artist, and entrepreneur, to see if there's interest in
booking him to present the {config.BRAND_NAME} for your organization.

The presentation blends real talk on service, reinvention, and building
something from nothing — pulled directly from his own story:

{pillars_text}

Engagements typically start at {config.FEE_TIERS[fee_tier]}, and {config.EPK_LINE}

If this could be a fit for an upcoming event, reply here or reach out directly
at {config.BOOKING_EMAIL} / {config.BOOKING_PHONE} and we'll get a date on the
calendar.

Best,
{config.SPEAKER_NAME} — {config.BRAND_NAME}
{config.BOOKING_EMAIL}"""


def infer_fee_tier(lead):
    name = (lead.get("name") or "").lower()
    query = (lead.get("source_query") or "").lower()
    if "college" in name or "college" in query or "community org" in query:
        return "college_community_org"
    if "corporate" in query or "dei" in query or "chamber" in name:
        return "corporate_conference"
    return "school_nonprofit"


def compose_email(lead):
    fee_tier = infer_fee_tier(lead)

    if not config.ANTHROPIC_API_KEY:
        subject = f"Booking {config.SPEAKER_NAME} for {lead.get('name', 'your organization')}"
        return subject, _static_fallback(lead, fee_tier)

    pillars_text = "\n".join(f"- {n}: {d}" for n, d in config.PILLARS)
    user_prompt = f"""Organization: {lead.get('name')}
Address: {lead.get('address')}
Found via search: {lead.get('source_query')}
Suggested fee range for this org type: {config.FEE_TIERS[fee_tier]}

Full list of speaker pillars to choose from (pick 2-3 most relevant):
{pillars_text}

Booking contact to include: {config.BOOKING_EMAIL} / {config.BOOKING_PHONE}
EPK line to include near the end: {config.EPK_LINE}
"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        body = "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        if not body:
            raise ValueError("empty response")
        subject = f"Booking {config.SPEAKER_NAME} for {lead.get('name', 'your organization')}"
        return subject, body
    except Exception as e:
        print(f"[email_composer] Claude generation failed ({e}), using static template")
        subject = f"Booking {config.SPEAKER_NAME} for {lead.get('name', 'your organization')}"
        return subject, _static_fallback(lead, fee_tier)


if __name__ == "__main__":
    test_lead = {
        "name": "Example Community College",
        "address": "123 Main St, Vineland, NJ",
        "source_query": "community college student life events Philadelphia",
    }
    subj, body = compose_email(test_lead)
    print("SUBJECT:", subj)
    print()
    print(body)
