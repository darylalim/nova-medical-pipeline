from unittest.mock import MagicMock

import streamlit_app

FAKE_AUDIO = b"fake-audio-data"


def _word(text: str, confidence: float):
    w = MagicMock()
    w.punctuated_word = text
    w.confidence = confidence
    return w


class TestParseUrls:
    def test_empty_text_returns_no_urls(self):
        valid, invalid = streamlit_app._parse_urls("")
        assert valid == []
        assert invalid == []

    def test_blank_lines_are_skipped(self):
        valid, invalid = streamlit_app._parse_urls("  \n\n  \n")
        assert valid == []
        assert invalid == []

    def test_valid_http_url(self):
        valid, invalid = streamlit_app._parse_urls("http://example.com/audio.wav")
        assert valid == ["http://example.com/audio.wav"]
        assert invalid == []

    def test_valid_https_url(self):
        valid, invalid = streamlit_app._parse_urls("https://example.com/audio.wav")
        assert valid == ["https://example.com/audio.wav"]
        assert invalid == []

    def test_invalid_protocol_rejected(self):
        valid, invalid = streamlit_app._parse_urls("ftp://example.com/audio.wav")
        assert valid == []
        assert invalid == ["ftp://example.com/audio.wav"]

    def test_mixed_valid_and_invalid(self):
        text = (
            "https://example.com/a.wav\nftp://bad.com/b.wav\nhttp://example.com/c.mp3"
        )
        valid, invalid = streamlit_app._parse_urls(text)
        assert valid == ["https://example.com/a.wav", "http://example.com/c.mp3"]
        assert invalid == ["ftp://bad.com/b.wav"]


class TestProcessInputs:
    def test_creates_single_client_for_batch(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_inputs("test-key", [("a.wav", b"a"), ("b.wav", b"b")])

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        assert mock_client.listen.v1.media.transcribe_file.call_count == 2

    def test_passes_correct_transcribe_options(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_inputs("test-key", [("test.wav", FAKE_AUDIO)])

        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.assert_called_once_with(
            request=FAKE_AUDIO,
            model="nova-3-medical",
            smart_format=True,
            numerals=True,
            profanity_filter=True,
        )

    def test_stores_responses_in_session_state(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_inputs("test-key", [("test.wav", FAKE_AUDIO)])

        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0][0] == "test.wav"

    def test_continues_after_single_file_failure(self, mock_deepgram_cls, mock_st):
        mock_client = mock_deepgram_cls.return_value
        good_response = MagicMock()
        mock_client.listen.v1.media.transcribe_file.side_effect = [
            Exception("API error"),
            good_response,
        ]

        streamlit_app._process_inputs(
            "test-key", [("bad.wav", b"bad"), ("good.wav", b"good")]
        )

        mock_st.error.assert_called_once_with(
            "Transcription failed for bad.wav: API error"
        )
        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0] == ("good.wav", good_response)

    def test_all_files_failing_does_not_set_session_state(
        self, mock_deepgram_cls, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.side_effect = Exception("fail")

        streamlit_app._process_inputs("test-key", [("a.wav", b"a"), ("b.wav", b"b")])

        assert mock_st.error.call_count == 2
        assert "responses" not in mock_st.session_state

    def test_stores_all_successful_responses(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_inputs(
            "test-key", [("a.wav", b"a"), ("b.wav", b"b"), ("c.wav", b"c")]
        )

        responses = mock_st.session_state["responses"]
        assert len(responses) == 3
        assert [name for name, _ in responses] == ["a.wav", "b.wav", "c.wav"]

    def test_error_message_includes_filename_and_exception(
        self, mock_deepgram_cls, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_file.side_effect = Exception("timeout")

        streamlit_app._process_inputs("test-key", [("bad.wav", b"bad")])

        mock_st.error.assert_called_once_with(
            "Transcription failed for bad.wav: timeout"
        )


class TestProcessUrls:
    def test_creates_single_client_for_batch(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_urls(
            "test-key", ["https://example.com/a.wav", "https://example.com/b.wav"]
        )

        mock_deepgram_cls.assert_called_once_with(api_key="test-key")
        mock_client = mock_deepgram_cls.return_value
        assert mock_client.listen.v1.media.transcribe_url.call_count == 2

    def test_passes_correct_transcribe_options(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_urls("test-key", ["https://example.com/test.wav"])

        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.assert_called_once_with(
            url="https://example.com/test.wav",
            model="nova-3-medical",
            smart_format=True,
            numerals=True,
            profanity_filter=True,
        )

    def test_stores_responses_in_session_state(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_urls("test-key", ["https://example.com/test.wav"])

        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0][0] == "https://example.com/test.wav"

    def test_continues_after_single_url_failure(self, mock_deepgram_cls, mock_st):
        mock_client = mock_deepgram_cls.return_value
        good_response = MagicMock()
        mock_client.listen.v1.media.transcribe_url.side_effect = [
            Exception("API error"),
            good_response,
        ]

        streamlit_app._process_urls(
            "test-key",
            ["https://example.com/bad.wav", "https://example.com/good.wav"],
        )

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: API error"
        )
        responses = mock_st.session_state["responses"]
        assert len(responses) == 1
        assert responses[0] == ("https://example.com/good.wav", good_response)

    def test_all_urls_failing_does_not_set_session_state(
        self, mock_deepgram_cls, mock_st
    ):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("fail")

        streamlit_app._process_urls(
            "test-key",
            ["https://example.com/a.wav", "https://example.com/b.wav"],
        )

        assert mock_st.error.call_count == 2
        assert "responses" not in mock_st.session_state

    def test_stores_all_successful_responses(self, mock_deepgram_cls, mock_st):
        streamlit_app._process_urls(
            "test-key",
            [
                "https://example.com/a.wav",
                "https://example.com/b.wav",
                "https://example.com/c.wav",
            ],
        )

        responses = mock_st.session_state["responses"]
        assert len(responses) == 3
        assert [name for name, _ in responses] == [
            "https://example.com/a.wav",
            "https://example.com/b.wav",
            "https://example.com/c.wav",
        ]

    def test_error_message_includes_url_and_exception(self, mock_deepgram_cls, mock_st):
        mock_client = mock_deepgram_cls.return_value
        mock_client.listen.v1.media.transcribe_url.side_effect = Exception("timeout")

        streamlit_app._process_urls("test-key", ["https://example.com/bad.wav"])

        mock_st.error.assert_called_once_with(
            "Transcription failed for https://example.com/bad.wav: timeout"
        )


class TestDisplayResponse:
    def test_offers_transcript_text_download(self, mock_deepgram_cls, mock_st):
        mock_response = (
            mock_deepgram_cls.return_value.listen.v1.media.transcribe_file.return_value
        )
        dl_txt, dl_json = MagicMock(), MagicMock()
        mock_st.columns.side_effect = [
            (MagicMock(), MagicMock(), MagicMock(), MagicMock()),
            (dl_txt, dl_json),
        ]

        streamlit_app._display_response("test.wav", mock_response)

        dl_txt.download_button.assert_called_once_with(
            "Download Transcript",
            data="Life moves pretty fast.",
            file_name="test.wav.txt",
            mime="text/plain",
            key="download_txt_test.wav",
        )

    def test_offers_json_download(self, mock_deepgram_cls, mock_st):
        mock_response = (
            mock_deepgram_cls.return_value.listen.v1.media.transcribe_file.return_value
        )
        dl_txt, dl_json = MagicMock(), MagicMock()
        mock_st.columns.side_effect = [
            (MagicMock(), MagicMock(), MagicMock(), MagicMock()),
            (dl_txt, dl_json),
        ]

        streamlit_app._display_response("test.wav", mock_response)

        dl_json.download_button.assert_called_once_with(
            "Download JSON",
            data=mock_response.model_dump_json(indent=4),
            file_name="test.wav.json",
            mime="application/json",
            key="download_json_test.wav",
        )

    def test_displays_transcript_text(self, mock_deepgram_cls, mock_st):
        mock_response = (
            mock_deepgram_cls.return_value.listen.v1.media.transcribe_file.return_value
        )
        mock_st.columns.side_effect = [
            (MagicMock(), MagicMock(), MagicMock(), MagicMock()),
            (MagicMock(), MagicMock()),
        ]

        streamlit_app._display_response("test.wav", mock_response)

        mock_st.code.assert_called_once_with(
            "Life moves pretty fast.", language=None, wrap_lines=True
        )

    def test_displays_metrics(self, mock_deepgram_cls, mock_st):
        mock_response = (
            mock_deepgram_cls.return_value.listen.v1.media.transcribe_file.return_value
        )
        col1, col2, col3, col4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        mock_st.columns.side_effect = [
            (col1, col2, col3, col4),
            (MagicMock(), MagicMock()),
        ]

        streamlit_app._display_response("test.wav", mock_response)

        mock_st.subheader.assert_called_once_with("test.wav")
        col1.metric.assert_called_once_with("Confidence", "98.0%")
        col2.metric.assert_called_once_with("Duration", "3.5s")
        col3.metric.assert_called_once_with("Words", 5)
        col4.metric.assert_called_once_with("Language", "en")


class TestRenderTranscriptHtml:
    def test_empty_list_returns_empty_string(self):
        assert streamlit_app._render_transcript_html([]) == ""

    def test_all_high_confidence_no_marks(self):
        words = [_word("Hello", 0.99), _word("world.", 0.97)]
        html = streamlit_app._render_transcript_html(words)
        assert "<mark>" not in html
        assert html == "Hello world."

    def test_all_low_confidence_every_word_wrapped(self):
        words = [_word("Hello", 0.80), _word("world.", 0.75)]
        html = streamlit_app._render_transcript_html(words)
        assert html == "<mark>Hello</mark> <mark>world.</mark>"

    def test_mixed_confidences_only_low_wrapped(self):
        words = [
            _word("The", 0.99),
            _word("patient", 0.85),  # below 0.90
            _word("presents.", 0.95),
        ]
        html = streamlit_app._render_transcript_html(words)
        assert html == "The <mark>patient</mark> presents."

    def test_threshold_boundary_0_90_not_wrapped(self):
        # < 0.90 wraps; 0.90 itself does not.
        words = [_word("borderline", 0.90)]
        assert streamlit_app._render_transcript_html(words) == "borderline"

    def test_uses_punctuated_word_not_word(self):
        w = MagicMock()
        w.punctuated_word = "Doctor,"
        w.word = "doctor"
        w.confidence = 0.99
        assert streamlit_app._render_transcript_html([w]) == "Doctor,"
