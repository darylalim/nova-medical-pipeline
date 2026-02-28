from unittest.mock import MagicMock

import streamlit_app

FAKE_AUDIO = b"fake-audio-data"


class TestProcessInputs:
    def test_creates_single_client_for_batch(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_inputs([("a.wav", b"a"), ("b.wav", b"b")])

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        assert mock_client.listen.v1.media.transcribe_file.call_count == 2

    def test_passes_correct_transcribe_options(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_inputs([("test.wav", FAKE_AUDIO)])

        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.assert_called_once_with(
            request=FAKE_AUDIO,
            model="nova-3-medical",
            smart_format=True,
            numerals=True,
            profanity_filter=True,
        )

    def test_stores_responses_in_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_inputs([("test.wav", FAKE_AUDIO)])

        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0][0] == "test.wav"

    def test_missing_api_key_shows_error(self, mock_deepgram_cls, monkeypatch, mock_st):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        streamlit_app._process_inputs([("test.wav", FAKE_AUDIO)])

        mock_st.error.assert_called_once_with(
            "Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root."
        )
        assert "responses" not in mock_st.session_state

    def test_continues_after_single_file_failure(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        good_response = MagicMock()
        mock_client.listen.v1.media.transcribe_file.side_effect = [
            Exception("API error"),
            good_response,
        ]

        streamlit_app._process_inputs([("bad.wav", b"bad"), ("good.wav", b"good")])

        mock_st.error.assert_called_once_with("Transcription failed for bad.wav: API error")
        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0] == ("good.wav", good_response)

    def test_all_files_failing_does_not_set_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.side_effect = Exception("fail")

        streamlit_app._process_inputs([("a.wav", b"a"), ("b.wav", b"b")])

        assert mock_st.error.call_count == 2
        assert "responses" not in mock_st.session_state

    def test_stores_all_successful_responses(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_inputs(
            [("a.wav", b"a"), ("b.wav", b"b"), ("c.wav", b"c")]
        )

        responses = mock_st.session_state["responses"]
        assert len(responses) == 3
        assert [name for name, _ in responses] == ["a.wav", "b.wav", "c.wav"]

    def test_error_message_includes_filename_and_exception(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.side_effect = Exception("timeout")

        streamlit_app._process_inputs([("bad.wav", b"bad")])

        mock_st.error.assert_called_once_with(
            "Transcription failed for bad.wav: timeout"
        )


class TestProcessUrls:
    def test_creates_single_client_for_batch(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(
            ["https://example.com/a.wav", "https://example.com/b.wav"]
        )

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        assert mock_client.listen.v1.media.transcribe_url.call_count == 2

    def test_passes_correct_transcribe_options(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(["https://example.com/test.wav"])

        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.assert_called_once_with(
            url="https://example.com/test.wav",
            model="nova-3-medical",
            smart_format=True,
            numerals=True,
            profanity_filter=True,
        )

    def test_stores_responses_in_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(["https://example.com/test.wav"])

        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0][0] == "https://example.com/test.wav"

    def test_missing_api_key_shows_error(self, mock_deepgram_cls, monkeypatch, mock_st):
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

        streamlit_app._process_urls(["https://example.com/test.wav"])

        mock_st.error.assert_called_once_with(
            "Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root."
        )
        assert "responses" not in mock_st.session_state

    def test_continues_after_single_url_failure(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        good_response = MagicMock()
        mock_client.listen.v1.media.transcribe_url.side_effect = [
            Exception("API error"),
            good_response,
        ]

        streamlit_app._process_urls(
            ["https://example.com/bad.wav", "https://example.com/good.wav"]
        )

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: API error"
        )
        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0] == ("https://example.com/good.wav", good_response)

    def test_all_urls_failing_does_not_set_session_state(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("fail")

        streamlit_app._process_urls(
            ["https://example.com/a.wav", "https://example.com/b.wav"]
        )

        assert mock_st.error.call_count == 2
        assert "responses" not in mock_st.session_state

    def test_stores_all_successful_responses(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        streamlit_app._process_urls(
            [
                "https://example.com/a.wav",
                "https://example.com/b.wav",
                "https://example.com/c.wav",
            ]
        )

        responses = mock_st.session_state["responses"]
        assert len(responses) == 3
        assert [name for name, _ in responses] == [
            "https://example.com/a.wav",
            "https://example.com/b.wav",
            "https://example.com/c.wav",
        ]

    def test_error_message_includes_url_and_exception(
        self, mock_deepgram_cls, env_with_api_key, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("timeout")

        streamlit_app._process_urls(["https://example.com/bad.wav"])

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: timeout"
        )
