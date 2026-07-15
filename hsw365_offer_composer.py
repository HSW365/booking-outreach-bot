"""
hsw365_offer_composer.py — builds the 3-touch email sequence for the HSW365
Front Desk + Website offer campaign. Templates are static (not LLM-generated)
so the copy always exactly matches the approved script in the calltwin repo
(docs/hsw365_frontdesk_website_agent.md) and the CallTwin agent's SMS copy.
"""

import config


def _first_name(lead):
    name = (lead.get("name") or "").strip()
    # Places results are business names, not people — fall back to a
    # friendly generic greeting rather than guessing a person's name.
    return name if name else "there"


def compose_touch1(lead):
    business = lead.get("name", "your business")
    subject = "Is your business missing calls right now?"
    body = f"""Hi {_first_name(lead)},

I'm reaching out from {config.OFFER_FROM_NAME} — we're a veteran-owned company based in Vineland, NJ.

Quick question: how many calls does {business} miss in a week — after hours, during a rush, on a day off?

We build two things for local businesses like yours:
1. A modern, mobile-friendly website, live in 48-72 hours.
2. A 24/7 AI Front Desk Assistant that answers every call and text automatically, so no customer ever hits voicemail again.

We already run this exact technology for our own company, so it's proven, not a pitch.

Want me to send over a free demo of what your site + front desk assistant would look like? No cost to see it: {config.OFFER_FUNNEL_LINK}

— {config.OFFER_FROM_NAME}
{config.OFFER_REPLY_TO}"""
    return subject, body


def compose_touch2(lead):
    business = lead.get("name", "your business")
    subject = "Free demo — no cost to look"
    body = f"""Hi {_first_name(lead)},

Following up in case this got buried. Happy to build you a free, no-obligation demo showing what a modern site + 24/7 front desk assistant would look like for {business}.

Takes us a couple minutes, costs you nothing. Want me to send it over? {config.OFFER_FUNNEL_LINK}

— {config.OFFER_FROM_NAME}"""
    return subject, body


def compose_touch3(lead):
    subject = f"Last note from {config.OFFER_FROM_NAME}"
    body = f"""Hi {_first_name(lead)},

Last note on this — if losing calls or not having an updated site isn't a priority right now, no worries at all. Reply anytime if that changes.

— {config.OFFER_FROM_NAME}"""
    return subject, body


TOUCH_COMPOSERS = {
    1: compose_touch1,
    2: compose_touch2,
    3: compose_touch3,
}


if __name__ == "__main__":
    test_lead = {"name": "Example Auto Repair", "address": "123 Main St, Vineland, NJ"}
    for n in (1, 2, 3):
        subj, body = TOUCH_COMPOSERS[n](test_lead)
        print(f"--- TOUCH {n} ---")
        print("SUBJECT:", subj)
        print()
        print(body)
        print()
