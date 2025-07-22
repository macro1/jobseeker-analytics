from utils import auth_utils
from unittest import mock

from fastapi import Request
from google.oauth2.credentials import Credentials

from db.processing_tasks import TaskRuns, FINISHED, STARTED
from routes.email_routes import fetch_emails_to_db


def test_processing(logged_in_client, started_task):
    # make request to check on processing status
    resp = logged_in_client.get("/processing", follow_redirects=False)
    # assert response
    assert resp.status_code == 200, resp.headers
    assert resp.json()["processed_emails"] == 0


def test_processing_404(logged_in_client):
    resp = logged_in_client.get("/processing", follow_redirects=False)
    assert resp.status_code == 404


def test_processing_redirect(incognito_client):
    resp = incognito_client.get("/processing", follow_redirects=False)
    assert resp.status_code == 303


def test_fetch_emails_to_db(logged_in_user, db_session):
    with mock.patch("routes.email_routes.get_email_ids", return_value=[]):
        fetch_emails_to_db(
            auth_utils.AuthenticatedUser(Credentials("abc")),
            Request({"type": "http", "session": {}}),
            user_id=logged_in_user.user_id,
        )

        task_run = db_session.get(TaskRuns, logged_in_user.user_id)
        assert task_run.status == FINISHED


def test_fetch_emails_to_db_in_progress_rate_limited_no_processing(
    logged_in_user, rate_limited_task, db_session
):
    with mock.patch(
        "routes.email_routes.get_email_ids", return_value=[]
    ) as mock_get_email_ids:
        fetch_emails_to_db(
            auth_utils.AuthenticatedUser(Credentials("abc")),
            Request({"type": "http", "session": {}}),
            user_id=logged_in_user.user_id,
        )

        mock_get_email_ids.assert_not_called()
        # Re-fetch the task from the db to ensure we have the latest state
        task_run = db_session.get(TaskRuns, logged_in_user.user_id)
        assert task_run.status == STARTED
