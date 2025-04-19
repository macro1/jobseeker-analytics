from routes.email_routes import fetch_emails_to_db
from utils import auth_utils
from fastapi import Request
from unittest import mock
from datetime import datetime
from db.users import Users
from db.processing_tasks import TaskRuns, FINISHED
from sqlalchemy.orm import Session

from google.oauth2.credentials import Credentials


def test_fetch_emails_to_db(session: Session):
    test_user_id = "123"

    session.add(
        Users(
            user_id=test_user_id,
            user_email="user123@example.com",
            start_date=datetime(2000, 1, 1),
        )
    )
    session.commit()

    with mock.patch("routes.email_routes.get_email_ids"):
        fetch_emails_to_db(
            auth_utils.AuthenticatedUser(Credentials("abc")),
            Request({"type": "http", "session": {}}),
            user_id=test_user_id,
        )

    task_run = session.get(TaskRuns, test_user_id)
    assert task_run.status == FINISHED
