from unittest import mock
import logging
from utils.llm_utils import process_email

@mock.patch("utils.llm_utils.processed_emails_exceeds_rate_limit", return_value=True)
@mock.patch("utils.llm_utils.model.generate_content")
def test_process_email_returns_with_429_if_batch_size_reached(mock_process_email, mock_rate_limit, caplog):
    caplog.set_level(logging.WARNING)
    mock_process_email.side_effect = Exception("429 Too Many Requests")
    process_email("test", "123")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert "Daily rate limit exceeded" in caplog.records[0].message
    
