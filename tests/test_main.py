import pytest

import main

FAKE_AUDIO = b"fake-audio-data"


class TestTranscribe:
    def test_calls_deepgram_with_correct_args(
        self, mock_deepgram_cls, env_with_api_key
    ):
        main.transcribe(FAKE_AUDIO)

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.assert_called_once_with(
            request=FAKE_AUDIO,
            model="nova-3",
            smart_format=True,
        )

    def test_returns_response_object(self, mock_deepgram_cls, env_with_api_key):
        response = main.transcribe(FAKE_AUDIO)

        assert response.results.channels[0].alternatives[0].transcript == "Life moves pretty fast."
        assert response.results.channels[0].alternatives[0].confidence == 0.98
        assert response.metadata.duration == 3.5

    def test_missing_api_key_raises_key_error(self, mock_deepgram_cls, monkeypatch):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        with pytest.raises(KeyError, match="DEEPGRAM_API_KEY"):
            main.transcribe(FAKE_AUDIO)
