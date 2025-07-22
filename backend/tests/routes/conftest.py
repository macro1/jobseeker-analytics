import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from db.users import Users
import database
import main
from session.session_layer import validate_session
from db.processing_tasks import STARTED, FINISHED, TaskRuns


@pytest.fixture
def task_factory(db_session, logged_in_user):
    def _create_task(status=STARTED, processed_emails=0):
        task = TaskRuns(
            user=logged_in_user, status=status, processed_emails=processed_emails
        )
        db_session.add(task)
        db_session.commit()
        return task

    return _create_task


@pytest.fixture
def user_factory(db_session):
    def _create_user(
        user_id="123", user_email="user@example.com", start_date=datetime(2000, 1, 1)
    ):
        user = Users(user_id=user_id, user_email=user_email, start_date=start_date)
        db_session.add(user)
        db_session.commit()
        return user

    return _create_user


@pytest.fixture
def logged_in_user(user_factory):
    return user_factory()


@pytest.fixture
def started_task(task_factory):
    return task_factory(status=STARTED)


@pytest.fixture
def finished_task(task_factory):
    return task_factory(status=FINISHED)


@pytest.fixture
def rate_limited_task(task_factory):
    return task_factory(status=STARTED, processed_emails=300)


@pytest.fixture
def client_factory(db_session):
    def _make_client(user=None):
        main.app.dependency_overrides[database.request_session] = lambda: db_session
        if user and user.user_id:
            main.app.dependency_overrides[validate_session] = lambda: user.user_id
        else:
            # Simulate not logged in: validate_session returns empty string
            main.app.dependency_overrides[validate_session] = lambda: ""
        return TestClient(main.app)

    return _make_client


@pytest.fixture
def logged_in_client(client_factory, logged_in_user):
    return client_factory(user=logged_in_user)


@pytest.fixture
def incognito_client(client_factory):
    return client_factory(user=None)
