"""
HSW365 Booking Outreach Bot — Configuration
Elvin "Ali" Torres Sr. / HOODSTAR ENT LLC / HSW365Media LLC

All values below can be overridden with environment variables of the
same name. Nothing here is a secret — API keys and credentials are
pulled from the environment only (see README.md).
"""

import os

# ---------------------------------------------------------------------------
# IDENTITY / PITCH CONTENT
# ---------------------------------------------------------------------------

SPEAKER_NAME = "Elvin \"Ali\" Torres Sr."
BRAND_NAME = "HSW365 Live Experience"
TOUR_NAME = "The Journey Continues – Inspired to Inspire Tour"

BOOKING_EMAIL = "book@hoodstar365.com"
BOOKING_PHONE = "(856) 796-8081"
BUSINESS_EMAIL = "hsw365media@gmail.com"

# The five pillars used in every pitch email. Keep these short — they get
# dropped into a bullet list in the email body.
PILLARS = [
    ("Army Veteran & Motivational Speaker",
     "First-hand story of service, struggle, and reinvention — built for "
     "assemblies, veteran programs, and leadership events."),
    ("Respect Da Game Podcast",
     "Hosts real conversations on hustle, mindset, and second chances — "
     "clips and co-branded episodes available for partner orgs."),
    ("Published Author",
     "\"Hoodlum Soldier,\" \"Ride Out,\" and \"God, Who Am I?\" — books "
     "available for classroom/library programs and author talks."),
    ("Recording Artist",
     "HOODSTAR365 label artist — live or recorded performance segments "
     "available as part of the presentation."),
    ("App Developer & Entrepreneur",
     "Built SpeekZone, QUEENEE, and CallTwin from the ground up — a real "
     "tech-entrepreneurship story for STEM/business audiences."),
    ("Streetwear Founder — HOODSTARWORLD",
     "Founder of a hand-bleached, one-of-one streetwear line — a live "
     "case study in building a brand from nothing."),
]

# Fee tiers referenced in outreach (from existing EPK / press kit)
FEE_TIERS = {
    "school_nonprofit": "$3,500 – $5,000",
    "college_community_org": "$5,000 – $7,500",
    "corporate_conference": "$7,500 – $10,000",
}

EPK_LINE = (
    "A full press kit / EPK with video, bio, and past engagement photos "
    "is available on request."
)

# ---------------------------------------------------------------------------
# LEAD TARGETING
# ---------------------------------------------------------------------------

# Google Places "type" + query-term combinations used to find booking leads.
# Tuned toward organizations that book speakers: schools, colleges, veteran
# orgs, libraries, community centers, chambers of commerce.
LEAD_SEARCH_QUERIES = [
    "high school assembly speaker programs South Jersey",
    "community college student life events Philadelphia",
    "veteran service organization events New Jersey",
    "public library author speaker series South Jersey",
    "community center youth programs Vineland NJ",
    "chamber of commerce business events South Jersey",
    "nonprofit youth mentorship organization Philadelphia",
    "corporate DEI speaker series Philadelphia",
]

# Geographic anchor for Places API radius search (Vineland, NJ)
SEARCH_LAT = 39.4864
SEARCH_LNG = -75.0257
SEARCH_RADIUS_METERS = 80000  # ~50 miles, covers South Jersey + Philly metro

# Contact page paths to check when scraping a lead's website for an email
CONTACT_PATH_CANDIDATES = [
    "", "contact", "contact-us", "about", "about-us", "staff", "team",
]

# ---------------------------------------------------------------------------
# SENDING
# ---------------------------------------------------------------------------

SEND_PROVIDER = os.environ.get("SEND_PROVIDER", "smtp")  # smtp | sendgrid
FROM_EMAIL = os.environ.get("FROM_EMAIL", BOOKING_EMAIL)
FROM_NAME = os.environ.get("FROM_NAME", f"{SPEAKER_NAME} — HSW365")
REPLY_TO = os.environ.get("REPLY_TO", BOOKING_EMAIL)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")          # e.g. hsw365media@gmail.com
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # Gmail App Password, not the login password

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

# Throttling — stay well under any provider's daily send limits and avoid
# looking automated to spam filters.
MAX_EMAILS_PER_RUN = int(os.environ.get("MAX_EMAILS_PER_RUN", "8"))
FOLLOWUP_AFTER_DAYS = int(os.environ.get("FOLLOWUP_AFTER_DAYS", "7"))
MAX_FOLLOWUPS = int(os.environ.get("MAX_FOLLOWUPS", "2"))

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
LOG_FILE = os.path.join(DATA_DIR, "contacted_log.json")

# ---------------------------------------------------------------------------
# CAMPAIGN 2: HSW365 FRONT DESK + WEBSITE OFFER
# Separate from the speaker-booking campaign above. Sells local business
# owners on the HSW365Media Modern Website + 24/7 AI Front Desk Assistant
# bundle — same "clone agent" persona used by the CallTwin calling script
# (see calltwin repo: docs/hsw365_frontdesk_website_agent.md).
# ---------------------------------------------------------------------------

OFFER_FROM_NAME = os.environ.get("OFFER_FROM_NAME", "HSW365Media")
OFFER_FROM_EMAIL = os.environ.get("OFFER_FROM_EMAIL", BUSINESS_EMAIL)  # hsw365media@gmail.com
OFFER_REPLY_TO = os.environ.get("OFFER_REPLY_TO", BOOKING_EMAIL)       # book@hoodstar365.com

# Live demo / signup page for this offer (QUEENEE.io free-demo flow).
OFFER_FUNNEL_LINK = os.environ.get(
    "OFFER_FUNNEL_LINK", "https://hsw365.github.io/QUEENEE.github.io/signup.html"
)

# Same ICP as calltwin_lead_hunter.py — local service businesses that are
# most likely to be losing money on missed calls / an outdated or missing
# website. Text-search queries for the Places API (New), same market radius
# as the booking campaign (South Jersey / Philly metro, see SEARCH_LAT/LNG).
OFFER_SEARCH_QUERIES = [
    "auto repair shop South Jersey",
    "hair salon South Jersey",
    "barbershop South Jersey",
    "nail salon South Jersey",
    "restaurant Vineland NJ",
    "plumber South Jersey",
    "electrician South Jersey",
    "landscaping company South Jersey",
    "cleaning service South Jersey",
    "daycare center South Jersey",
    "tax preparer South Jersey",
    "insurance agency South Jersey",
    "real estate agent South Jersey",
    "law office South Jersey",
    "dentist South Jersey",
    "chiropractor South Jersey",
    "auto repair shop Camden NJ",
    "restaurant Cherry Hill NJ",
    "salon Pennsauken NJ",
]

OFFER_DATA_DIR = os.environ.get("OFFER_DATA_DIR", DATA_DIR)
OFFER_LEADS_FILE = os.path.join(OFFER_DATA_DIR, "hsw365_offer_leads.json")
OFFER_LOG_FILE = os.path.join(OFFER_DATA_DIR, "hsw365_offer_contacted_log.json")

OFFER_MAX_EMAILS_PER_RUN = int(os.environ.get("OFFER_MAX_EMAILS_PER_RUN", "8"))
# Touch 2 fires ~3-4 days after touch 1, touch 3 ~7 days after touch 2 —
# matches the SMS sequence timing in the CallTwin agent script.
OFFER_TOUCH2_AFTER_DAYS = int(os.environ.get("OFFER_TOUCH2_AFTER_DAYS", "4"))
OFFER_TOUCH3_AFTER_DAYS = int(os.environ.get("OFFER_TOUCH3_AFTER_DAYS", "7"))
