"""
This file contains the main constants used in the application.
"""


from datetime import datetime, timedelta
from pathlib import Path
from utils.filter_utils import parse_filter_config


GENERIC_ATS_DOMAINS = [
    "us.greenhouse-mail.io",
    "smartrecruiters.com",
    "linkedin.com",
    "ashbyhq.com",
    "hire.lever.co",
    "hi.wellfound.com",
    "talent.icims.com",
    "myworkday.com",
    "otta.com",
]

DEFAULT_DAYS_AGO = 365 * 2
# Get the current date
current_date = datetime.now()

# Subtract 30 days
date_days_ago = current_date - timedelta(days=DEFAULT_DAYS_AGO)

# Format the date in the required format (YYYY/MM/DD)
formatted_date = date_days_ago.strftime("%Y/%m/%d")

FILTER_PATH = Path.cwd() / "email_query_filters" / "applied_email_filter.yaml"
QUERY_APPLIED_EMAIL_FILTER = f"after:{formatted_date} AND {parse_filter_config(FILTER_PATH)}"
# label:jobs -label:query4