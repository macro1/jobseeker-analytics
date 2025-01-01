import re
from email_validator import validate_email, EmailNotValidError
from installation_utils import get_file_path
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import logging
from auth_utils import AuthenticatedUser

logger = logging.getLogger(__name__)

def get_user() -> AuthenticatedUser:
    """Handles the OAuth2 flow and retrieves user credentials."""
    creds = None
    logger.info("Checking for existing credentials...")
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    CLIENT_SECRETS_FILE = "credentials.json"

    # Try to load existing credentials from token.json
    if os.path.exists('token.json'):
        logger.info("Loading existing credentials...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found. Redirecting to authorization URL...")
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES, redirect_uri="https://jobseeker-analytics.onrender.com/get-jobs"
            )
            authorization_url, state = flow.authorization_url(prompt="consent")
            logger.info(f"Authorization URL: {authorization_url}")
            logger.info(f"State: {state}")
            return authorization_url  # Return the authorization URL for user to visit

    # Save credentials for the next run
    with open('token.json', 'w') as token_file:
        logger.info("Saving credentials...")
        token_file.write(creds.to_json())

    return AuthenticatedUser(creds)
    


def is_automated_email(email: str) -> bool:
    """
    Determines if an email address is automated or from a person.

    Parameters:
    email (str): The email address to classify.

    Returns:
    bool: True if automated, False otherwise.
    """
    # Define patterns for common automated prefixes and domains
    automated_patterns = [
        r"^no[-_.]?reply@",  # Matches "no-reply", "no_reply", "noreply"
        r"^do[-_.]?not[-_.]?reply@",  # Matches "do-not-reply", "do_not_reply"
        r"^notifications@",  # Matches "notifications@"
        r"^team@",  # Matches "team@"
        r"^hello@",  # Matches "hello@" (often automated)
        r"@smartrecruiters\.com$",  # Matches specific automated domains
    ]

    # Check against the patterns
    for pattern in automated_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            return True  # It's an automated email

    return False  # It's likely from a person


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        print(str(e))
        return False


def get_email(id: str, gmail_instance=None):
    if gmail_instance:
        return gmail_instance.users().messages().get(userId="me", id=id).execute()


def get_email_ids(query: tuple = None, days_ago: int = 90, gmail_instance=None):
    if gmail_instance:
        return (
            gmail_instance.users()
            .messages()
            .list(
                userId="me",
                q=query,
                includeSpamTrash=True,
            )
            .execute()
        )


def get_id(msg):
    return msg.get("id", None)


def get_email_payload(msg):
    return msg.get("payload", None)


def get_email_headers(msg):
    email_data = get_email_payload(msg)
    if email_data:
        return email_data.get("headers", None)
    return None


def get_email_parts(msg):
    email_data = get_email_payload(msg)
    if email_data:
        return email_data.get("parts", None)
    return None


def get_email_subject_line(msg):
    try:
        email_headers = get_email_headers(msg)
        if email_headers:
            for header in email_headers:
                key = header.get("name")  # convert to dict for O(1) lookup ?
                if key == "Subject":
                    return header.get("value", "")
    except Exception as e:
        logger.error(f"Error getting email subject line: {e}")
    return ""


def get_email_from_address(msg):
    try:
        email_headers = get_email_headers(msg)
        if email_headers:
            for header in email_headers:
                if header.get("name") == "From":
                    # if value enclosed in <> then extract email address
                    # else return the value as is
                    from_address = header.get("value")
                    if "<" in from_address:
                        return from_address.split("<")[1].split(">")[0]
                    return from_address
    except Exception as e:
        logger.error(f"Error getting email from address: {e}")
    return ""


def get_received_at_timestamp(id, msg):
    import datetime

    try:
        email_headers = get_email_headers(msg)
        if email_headers:
            for header in email_headers:
                key = header.get("name")
                if key == "Date":
                    return header.get("value")
    except Exception as e:
        print(f"msg_{id}: {e}")
    return datetime.datetime.now()  # default if trouble parsing


def get_email_domain_from_address(email_address):
    return email_address.split("@")[1] if "@" in email_address else ""


def clean_email(email_body: str) -> list:
    import spacy
    from spacy_cleaner import processing, Cleaner

    try:
        model = spacy.load("en_core_web_sm")
        pipeline = Cleaner(
            model,
            processing.remove_stopword_token,
            processing.remove_punctuation_token,
            processing.remove_number_token,
        )
        return pipeline.clean([email_body])
    except Exception as e:
        logger.error(f"Error cleaning email: {e}")
    return []


def get_word_frequency(cleaned_email):
    try:
        word_dict = {}
        for word in cleaned_email[0].split(" "):
            if word not in word_dict:
                word_dict[word] = 1
            else:
                word_dict[word] += 1

        word_dict_sorted = sorted(word_dict.items(), key=lambda item: item[1], reverse=True)
        return word_dict_sorted
    except Exception as e:
        logger.error(f"Error getting word frequency: {e}")
    return []


def get_top_word_in_email_body(msg_id, msg):
    import base64
    from bs4 import BeautifulSoup

    try:
        parts = get_email_parts(msg)
        if parts:
            for part in parts:
                if part.get("mimeType") not in [
                    "text/plain",
                    "text/html",
                ]:
                    continue
                if part.get("mimeType") and part.get("mimeType") in [
                    "text/plain",
                    "text/html",
                ]:
                    data = base64.urlsafe_b64decode(
                        part.get("body", {}).get("data", {})
                    ).decode("utf-8")
                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(data, "html.parser")
                    # Extract the plain text from the HTML content
                    email_text = soup.get_text()
                    cleaned_text = clean_email(email_text)
                    # write to file for debugging
                    # with open(f"data/{msg_id}.txt", "w") as f:
                    #     f.write(email_text)
                    # with open(f"data/{msg_id}_cleaned.txt", "w") as f:
                    #     f.write(cleaned_text[0])
                    if cleaned_text:
                        word_frequency = get_word_frequency(cleaned_text)
                        # with open(f"data/{msg_id}_word_frequency.txt", "w") as f:
                        #     f.write(str(word_frequency))
                        top_capitalized_word = get_top_consecutive_capitalized_words(
                            word_frequency
                        )
                        if not top_capitalized_word:
                            if len(cleaned_text) > 0:
                                return cleaned_text[0]
                        return top_capitalized_word or cleaned_text[0][0]
    except Exception as e:
        logger.error(f"Error getting top word: {e}")
    return ""


def get_company_name(id, msg):
    try:
        top_word = get_top_word_in_email_body(id, msg)
        if not top_word:
            # likely a calendar invite, haven't parsed these yet
            # return email domain instead as shortcut
            # TODO: compare email domain and top word to decide
            from_address = get_email_from_address(msg)
            return get_email_domain_from_address(from_address).split(".")[0]
        return top_word
    except Exception as e:
        logger.error(f"Error getting company name: {e}")
    return ""


def get_top_consecutive_capitalized_words(tuples_list):
    """
    Helper function to parse company name from an email.
    We only want the top capitalized words that appear consecutively and with the same frequency.
    """
    try:
        result = []
        temp_group = []
        max = float("-inf")
        for i, (first, second) in enumerate(tuples_list):
            is_capitalized = first and first[0].isupper()

            if is_capitalized:
                if not temp_group:
                    max = second
                    temp_group.append((first, second))
                if temp_group and temp_group[-1][1] == second:
                    # Add to the current group if criteria match
                    temp_group.append((first, second))
                if second < max:
                    break
                result.append(first)
        return " ".join(result)
    except Exception as e:
        logger.error(f"Error getting top consecutive capitalized words: {e}")
    return ""