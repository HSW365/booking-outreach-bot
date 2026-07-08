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
