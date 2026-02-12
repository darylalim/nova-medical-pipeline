from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_deepgram_cls():
    with patch("main.DeepgramClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = '{"results": "transcribed"}'
        mock_cls.return_value.listen.v1.media.transcribe_file.return_value = (
            mock_response
        )
        yield mock_cls


@pytest.fixture
def env_with_api_key(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
