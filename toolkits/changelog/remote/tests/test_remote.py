from __future__ import annotations

import ast
import contextlib
import importlib
import io
import json
import os
import socket
import tempfile
import threading
import time
import traceback
import unittest
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import BaseRequestHandler, ThreadingTCPServer
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import ph_changelog_remote.cli as cli_module
from ph_changelog_remote.cli import build_parser, main
from ph_changelog_remote.fetch import (
    ACCEPT,
    MAX_REDIRECTS,
    USER_AGENT,
    FetchResult,
    RemoteFetchError,
    _redirect_url,
    fetch_changelog,
)

VALID_RAW = (
    b"# Changelog\n\n"
    b"All notable changes.\n\n"
    b"## [Unreleased]\n\n"
    b"### Added\n"
    b"- Add remote inspection.\n"
)


@contextlib.contextmanager
def _running_tcp_server(handler: type[BaseRequestHandler]) -> Iterator[str]:
    server = ThreadingTCPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    server_thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01),
        daemon=True,
    )
    server_thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)


def _receive_request_headers(connection: object) -> bytes:
    received = bytearray()
    while b"\r\n\r\n" not in received:
        chunk = connection.recv(4096)
        if not chunk:
            break
        received.extend(chunk)
    return bytes(received)


class _Headers:
    def __init__(self, values: dict[str, str | list[str]] | None = None) -> None:
        self.values = {
            key.lower(): value if isinstance(value, list) else [value]
            for key, value in (values or {}).items()
        }

    def get(self, name: str) -> str | None:
        values = self.values.get(name.lower())
        return values[0] if values else None

    def get_all(self, name: str) -> list[str] | None:
        return self.values.get(name.lower())


class _Response:
    def __init__(
        self,
        raw: bytes = VALID_RAW,
        *,
        url: str = "https://example.test/CHANGELOG.md",
        status: int = 200,
        headers: dict[str, str | list[str]] | None = None,
    ) -> None:
        self.stream = io.BytesIO(raw)
        self.url = url
        self.status = status
        self.headers = _Headers(headers)
        self.read_calls = 0
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        return self.stream.read(size)

    def geturl(self) -> str:
        return self.url

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        self.closed = True
        self.stream.close()


class _Transport:
    def __init__(self, response: _Response | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.requests: list[Request] = []
        self.timeouts: list[float] = []

    def open(self, request: Request, *, timeout: float) -> _Response:
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


class _FailingResponse(_Response):
    def read(self, size: int = -1) -> bytes:
        raise OSError("read failed at https://example.test/CHANGELOG.md?token=hunter2")


class _BinaryStdout:
    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, value: str) -> int:
        raise AssertionError(f"text stdout path was used for {value!r}")


def _source() -> dict[str, object]:
    return {
        "kind": "http",
        "requested_url": "https://example.test/CHANGELOG.md",
        "final_url": "https://example.test/CHANGELOG.md",
        "query_redacted": False,
        "status": 200,
        "content_type": "text/plain",
        "etag": None,
        "last_modified": None,
    }


class UrlPolicyTests(unittest.TestCase):
    def test_https_request_has_bounded_public_headers(self) -> None:
        response = _Response(
            headers={
                "Content-Type": "text/markdown; charset=UTF-8",
                "ETag": '"revision-1"',
                "Last-Modified": "Fri, 14 Aug 2026 12:00:00 GMT",
            }
        )
        transport = _Transport(response)

        result = fetch_changelog(
            "https://example.test/CHANGELOG.md", timeout=2.5, transport=transport
        )

        request = transport.requests[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("User-agent"), USER_AGENT)
        self.assertEqual(request.get_header("Accept"), ACCEPT)
        self.assertEqual(request.get_header("Accept-encoding"), "identity")
        self.assertEqual(len(transport.timeouts), 1)
        self.assertAlmostEqual(transport.timeouts[0], 2.5, delta=0.01)
        self.assertEqual(result.raw, VALID_RAW)
        self.assertEqual(
            result.source,
            {
                "kind": "http",
                "requested_url": "https://example.test/CHANGELOG.md",
                "final_url": "https://example.test/CHANGELOG.md",
                "query_redacted": False,
                "status": 200,
                "content_type": "text/markdown",
                "etag": '"revision-1"',
                "last_modified": "Fri, 14 Aug 2026 12:00:00 GMT",
            },
        )
        self.assertTrue(response.closed)

    def test_query_is_sent_but_redacted_from_both_metadata_urls(self) -> None:
        response = _Response(
            url="https://cdn.test/CHANGELOG.md?signature=redirect-secret",
            headers={"Content-Type": "text/plain"},
        )
        transport = _Transport(response)
        requested = "https://example.test/CHANGELOG.md?token=request-secret"

        result = fetch_changelog(requested, transport=transport)

        self.assertEqual(transport.requests[0].full_url, requested)
        self.assertEqual(result.source["requested_url"], "https://example.test/CHANGELOG.md")
        self.assertEqual(result.source["final_url"], "https://cdn.test/CHANGELOG.md")
        self.assertIs(result.source["query_redacted"], True)
        serialized = json.dumps(result.source)
        self.assertNotIn("request-secret", serialized)
        self.assertNotIn("redirect-secret", serialized)

    def test_plain_http_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(RemoteFetchError, "--allow-http"):
            fetch_changelog("http://example.test/CHANGELOG.md", transport=_Transport())

        response = _Response(url="http://example.test/CHANGELOG.md")
        result = fetch_changelog(
            "http://example.test/CHANGELOG.md",
            allow_http=True,
            transport=_Transport(response),
        )
        self.assertEqual(result.source["final_url"], "http://example.test/CHANGELOG.md")

    def test_unsafe_or_malformed_urls_fail_before_transport(self) -> None:
        urls = (
            "ftp://example.test/CHANGELOG.md",
            "https:///CHANGELOG.md",
            "https://user:password@example.test/CHANGELOG.md",
            "https://example.test/CHANGELOG.md#release",
            "https://example.test/CHANGELOG.md\nInjected: header",
            "https://example.test/%0d%0aInjected",
            "https://example.test:0/CHANGELOG.md",
            "https://example.test:99999/CHANGELOG.md",
        )
        for url in urls:
            with self.subTest(url=url):
                transport = _Transport()
                with self.assertRaises(RemoteFetchError):
                    fetch_changelog(url, transport=transport)
                self.assertEqual(transport.requests, [])

    def test_final_url_is_revalidated_and_cannot_downgrade(self) -> None:
        response = _Response(url="http://example.test/CHANGELOG.md")
        with self.assertRaisesRegex(RemoteFetchError, "plain HTTP"):
            fetch_changelog(
                "https://example.test/CHANGELOG.md",
                allow_http=True,
                transport=_Transport(response),
            )
        self.assertTrue(response.closed)

    def test_redirect_policy_accepts_relative_https_targets(self) -> None:
        redirected = _redirect_url(
            "https://example.test/releases/CHANGELOG.md",
            "../latest.md",
            allow_http=False,
        )
        self.assertEqual(redirected, "https://example.test/latest.md")

    def test_redirect_policy_rejects_downgrade_even_when_http_is_allowed(self) -> None:
        with self.assertRaisesRegex(RemoteFetchError, "downgrade"):
            _redirect_url(
                "https://example.test/CHANGELOG.md",
                "http://example.test/CHANGELOG.md",
                allow_http=True,
            )

    def test_redirect_policy_revalidates_credentials_and_fragments(self) -> None:
        for target in (
            "https://user:secret@example.test/CHANGELOG.md",
            "https://example.test/CHANGELOG.md#fragment",
        ):
            with self.subTest(target=target):
                with self.assertRaises(RemoteFetchError):
                    _redirect_url(
                        "https://example.test/CHANGELOG.md",
                        target,
                        allow_http=False,
                    )


class ResponsePolicyTests(unittest.TestCase):
    def test_content_length_precheck_refuses_before_reading(self) -> None:
        response = _Response(headers={"Content-Length": "11"}, raw=b"small")
        with self.assertRaisesRegex(RemoteFetchError, "10-byte"):
            fetch_changelog(
                "https://example.test/CHANGELOG.md",
                max_bytes=10,
                transport=_Transport(response),
            )
        self.assertEqual(response.read_calls, 0)
        self.assertTrue(response.closed)

    def test_streaming_limit_detects_body_without_content_length(self) -> None:
        response = _Response(raw=b"123456")
        with self.assertRaisesRegex(RemoteFetchError, "5-byte"):
            fetch_changelog(
                "https://example.test/CHANGELOG.md",
                max_bytes=5,
                transport=_Transport(response),
            )
        self.assertTrue(response.closed)

    def test_exact_streaming_limit_is_accepted(self) -> None:
        response = _Response(raw=b"12345", headers={"Content-Length": "5"})
        result = fetch_changelog(
            "https://example.test/CHANGELOG.md",
            max_bytes=5,
            transport=_Transport(response),
        )
        self.assertEqual(result.raw, b"12345")

    def test_invalid_content_length_is_rejected(self) -> None:
        response = _Response(headers={"Content-Length": "+10"})
        with self.assertRaisesRegex(RemoteFetchError, "invalid Content-Length"):
            fetch_changelog("https://example.test/CHANGELOG.md", transport=_Transport(response))

    def test_content_length_must_exactly_match_received_body(self) -> None:
        for raw, declared in ((b"short", "10"), (b"too long", "3")):
            with self.subTest(raw=raw, declared=declared):
                response = _Response(raw=raw, headers={"Content-Length": declared})
                with self.assertRaisesRegex(RemoteFetchError, "expected"):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md",
                        transport=_Transport(response),
                    )

    def test_duplicate_content_length_is_rejected(self) -> None:
        response = _Response(headers={"Content-Length": ["5", "5"]})
        with self.assertRaisesRegex(RemoteFetchError, "must not be repeated"):
            fetch_changelog("https://example.test/CHANGELOG.md", transport=_Transport(response))

    def test_non_identity_content_encoding_is_rejected(self) -> None:
        response = _Response(headers={"Content-Encoding": "gzip"})
        with self.assertRaisesRegex(RemoteFetchError, "encoded responses"):
            fetch_changelog("https://example.test/CHANGELOG.md", transport=_Transport(response))

    def test_unsupported_or_ambiguous_codings_are_rejected(self) -> None:
        cases = (
            {"Transfer-Encoding": "gzip"},
            {"Transfer-Encoding": "gzip, chunked"},
            {"Transfer-Encoding": ["chunked", "gzip"]},
            {"Content-Encoding": ["identity", "gzip"]},
            {
                "Transfer-Encoding": "chunked",
                "Content-Length": str(len(VALID_RAW)),
            },
        )
        for headers in cases:
            with self.subTest(headers=headers):
                response = _Response(headers=headers)
                with self.assertRaises(RemoteFetchError):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md",
                        transport=_Transport(response),
                    )

    def test_single_chunked_transfer_coding_is_accepted_after_decoding(self) -> None:
        response = _Response(headers={"Transfer-Encoding": "chunked"})
        result = fetch_changelog(
            "https://example.test/CHANGELOG.md",
            transport=_Transport(response),
        )
        self.assertEqual(result.raw, VALID_RAW)

    def test_html_unrelated_and_malformed_media_types_are_rejected(self) -> None:
        for media_type in (
            "",
            "text/plain, text/html",
            "text/html",
            "application/xhtml+xml",
            "application/json",
            "image/png",
        ):
            with self.subTest(media_type=media_type):
                response = _Response(headers={"Content-Type": media_type})
                with self.assertRaisesRegex(RemoteFetchError, "unsupported response media"):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md", transport=_Transport(response)
                    )

    def test_generic_raw_file_media_types_are_accepted(self) -> None:
        for media_type in ("application/markdown", "application/octet-stream"):
            with self.subTest(media_type=media_type):
                response = _Response(headers={"Content-Type": media_type})
                result = fetch_changelog(
                    "https://example.test/CHANGELOG.md", transport=_Transport(response)
                )
                self.assertEqual(result.source["content_type"], media_type)

    def test_absent_content_type_is_recorded_as_null(self) -> None:
        result = fetch_changelog(
            "https://example.test/CHANGELOG.md", transport=_Transport(_Response())
        )
        self.assertIsNone(result.source["content_type"])

    def test_utf8_charset_alias_is_accepted(self) -> None:
        response = _Response(headers={"Content-Type": "text/plain; charset=utf8"})
        result = fetch_changelog(
            "https://example.test/CHANGELOG.md", transport=_Transport(response)
        )
        self.assertEqual(result.source["content_type"], "text/plain")

    def test_non_utf8_and_unknown_declared_charsets_are_rejected(self) -> None:
        for charset in ("iso-8859-1", "definitely-not-a-charset"):
            with self.subTest(charset=charset):
                response = _Response(headers={"Content-Type": f"text/plain; charset={charset}"})
                with self.assertRaisesRegex(RemoteFetchError, "charset"):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md", transport=_Transport(response)
                    )

    def test_body_must_decode_as_strict_utf8(self) -> None:
        response = _Response(raw=b"\xff", headers={"Content-Type": "text/plain"})
        with self.assertRaisesRegex(RemoteFetchError, "strict UTF-8"):
            fetch_changelog("https://example.test/CHANGELOG.md", transport=_Transport(response))

    def test_only_status_200_is_accepted_as_a_complete_snapshot(self) -> None:
        for status in (204, 206, 226, 304):
            with self.subTest(status=status):
                response = _Response(status=status)
                with self.assertRaisesRegex(RemoteFetchError, str(status)):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md",
                        transport=_Transport(response),
                    )
                self.assertTrue(response.closed)

    def test_status_200_with_content_range_is_rejected_as_partial(self) -> None:
        for value in ("bytes 0-43/1000", ["bytes 0-43/1000", "bytes 44-87/1000"]):
            with self.subTest(value=value):
                response = _Response(headers={"Content-Range": value})
                with self.assertRaisesRegex(RemoteFetchError, "partial Content-Range"):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md",
                        transport=_Transport(response),
                    )

    def test_timeout_and_size_options_fail_closed(self) -> None:
        for options in (
            {"timeout": 0},
            {"timeout": float("inf")},
            {"timeout": float("nan")},
            {"max_bytes": 0},
            {"max_bytes": True},
            {"allow_http": "false"},
            {"allow_http": 1},
        ):
            with self.subTest(options=options):
                with self.assertRaises(RemoteFetchError):
                    fetch_changelog(
                        "https://example.test/CHANGELOG.md",
                        transport=_Transport(),
                        **options,
                    )

    def test_http_and_network_errors_do_not_expose_query_secrets(self) -> None:
        url = "https://example.test/CHANGELOG.md?token=hunter2"
        errors = (
            HTTPError(url, 404, "Not Found", {}, None),
            URLError(f"connection failed for {url}"),
            RuntimeError(f"transport failed for {url}"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(RemoteFetchError) as caught:
                    fetch_changelog(url, transport=_Transport(error=error))
                message = str(caught.exception)
                self.assertNotIn("hunter2", message)
                self.assertNotIn("token", message)
                self.assertIsNone(caught.exception.__cause__)
                formatted = "".join(traceback.format_exception(caught.exception))
                self.assertNotIn("hunter2", formatted)

    def test_http_error_response_is_closed(self) -> None:
        body = io.BytesIO(b"error response")
        error = HTTPError(
            "https://example.test/CHANGELOG.md",
            404,
            "Not Found",
            {},
            body,
        )
        with self.assertRaises(RemoteFetchError):
            fetch_changelog(
                "https://example.test/CHANGELOG.md",
                transport=_Transport(error=error),
            )
        self.assertTrue(body.closed)

    def test_overall_deadline_rejects_slow_drip_body(self) -> None:
        clock = [0.0]

        class _DripResponse(_Response):
            def read(self, size: int = -1) -> bytes:
                clock[0] += 0.08
                return super().read(1)

        response = _DripResponse()
        with (
            patch("ph_changelog_remote.fetch.time.monotonic", side_effect=lambda: clock[0]),
            self.assertRaisesRegex(RemoteFetchError, "deadline"),
        ):
            fetch_changelog(
                "https://example.test/CHANGELOG.md",
                timeout=0.12,
                transport=_Transport(response),
            )
        self.assertTrue(response.closed)

    def test_real_slow_drip_cannot_extend_overall_deadline(self) -> None:
        class _SlowDripHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    for byte in VALID_RAW:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.08)
                except OSError:
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowDripHandler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(RemoteFetchError, "deadline"):
                fetch_changelog(
                    f"http://127.0.0.1:{server.server_port}/CHANGELOG.md",
                    allow_http=True,
                    timeout=0.12,
                )
            elapsed = time.monotonic() - started
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=1)

        self.assertLess(elapsed, 0.35)

    def test_real_slow_status_line_cannot_extend_overall_deadline(self) -> None:
        class _SlowStatusHandler(BaseRequestHandler):
            def handle(self) -> None:
                _receive_request_headers(self.request)
                response = (
                    b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n"
                )
                try:
                    for byte in response:
                        self.request.sendall(bytes([byte]))
                        time.sleep(0.04)
                except OSError:
                    pass

        with _running_tcp_server(_SlowStatusHandler) as origin:
            started = time.monotonic()
            with self.assertRaisesRegex(RemoteFetchError, "deadline"):
                fetch_changelog(
                    f"{origin}/CHANGELOG.md",
                    allow_http=True,
                    timeout=0.12,
                )
            elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.35)

    def test_slow_dns_returns_at_deadline_without_sending_request(self) -> None:
        request_seen = threading.Event()

        class _RequestRecordingHandler(BaseRequestHandler):
            def handle(self) -> None:
                _receive_request_headers(self.request)
                request_seen.set()
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(VALID_RAW)}\r\n".encode()
                    + b"Connection: close\r\n\r\n"
                    + VALID_RAW
                )

        original_getaddrinfo = socket.getaddrinfo

        def delayed_getaddrinfo(*args: object, **kwargs: object) -> object:
            time.sleep(0.25)
            return original_getaddrinfo(*args, **kwargs)

        with _running_tcp_server(_RequestRecordingHandler) as origin:
            started = time.monotonic()
            with (
                patch(
                    "ph_changelog_remote.fetch.socket.getaddrinfo",
                    side_effect=delayed_getaddrinfo,
                ),
                self.assertRaisesRegex(RemoteFetchError, "deadline"),
            ):
                fetch_changelog(
                    f"{origin}/CHANGELOG.md",
                    allow_http=True,
                    timeout=0.05,
                )
            elapsed = time.monotonic() - started
            self.assertFalse(request_seen.wait(timeout=0.35))

        self.assertLess(elapsed, 0.2)

    def test_real_slow_chunk_framing_cannot_extend_overall_deadline(self) -> None:
        class _SlowChunkHandler(BaseRequestHandler):
            def handle(self) -> None:
                _receive_request_headers(self.request)
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Transfer-Encoding: chunked\r\n"
                    b"Connection: close\r\n\r\n"
                )
                try:
                    for byte in b"1;slow-extension\r\n":
                        self.request.sendall(bytes([byte]))
                        time.sleep(0.04)
                except OSError:
                    pass

        with _running_tcp_server(_SlowChunkHandler) as origin:
            started = time.monotonic()
            with self.assertRaisesRegex(RemoteFetchError, "deadline"):
                fetch_changelog(
                    f"{origin}/CHANGELOG.md",
                    allow_http=True,
                    timeout=0.12,
                )
            elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.35)

    def test_real_chunked_response_is_decoded_and_accepted(self) -> None:
        class _ChunkedHandler(BaseRequestHandler):
            def handle(self) -> None:
                _receive_request_headers(self.request)
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Transfer-Encoding: chunked\r\n"
                    b"Connection: close\r\n\r\n"
                    + f"{len(VALID_RAW):X}\r\n".encode()
                    + VALID_RAW
                    + b"\r\n0\r\n\r\n"
                )

        with _running_tcp_server(_ChunkedHandler) as origin:
            result = fetch_changelog(
                f"{origin}/CHANGELOG.md",
                allow_http=True,
            )

        self.assertEqual(result.raw, VALID_RAW)

    def test_real_premature_eof_against_content_length_is_rejected(self) -> None:
        class _TruncatedHandler(BaseRequestHandler):
            def handle(self) -> None:
                _receive_request_headers(self.request)
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(VALID_RAW) + 100}\r\n".encode()
                    + b"Connection: close\r\n\r\n"
                    + VALID_RAW
                )

        with _running_tcp_server(_TruncatedHandler) as origin:
            with self.assertRaisesRegex(RemoteFetchError, "expected"):
                fetch_changelog(
                    f"{origin}/CHANGELOG.md",
                    allow_http=True,
                )

    def test_redirect_body_is_closed_without_being_drained(self) -> None:
        class _RedirectBodyHandler(BaseRequestHandler):
            def handle(self) -> None:
                request = _receive_request_headers(self.request)
                target = request.split(b" ", 2)[1]
                if target == b"/start":
                    self.request.sendall(
                        b"HTTP/1.1 302 Found\r\n"
                        b"Location: /final\r\n"
                        b"Content-Length: 1000000\r\n"
                        b"Connection: close\r\n\r\n"
                    )
                    try:
                        for _ in range(100):
                            self.request.sendall(b"x")
                            time.sleep(0.04)
                    except OSError:
                        pass
                    return

                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    + f"Content-Length: {len(VALID_RAW)}\r\n".encode()
                    + b"Connection: close\r\n\r\n"
                    + VALID_RAW
                )

        with _running_tcp_server(_RedirectBodyHandler) as origin:
            started = time.monotonic()
            result = fetch_changelog(
                f"{origin}/start",
                allow_http=True,
                timeout=0.5,
            )
            elapsed = time.monotonic() - started

        self.assertEqual(result.raw, VALID_RAW)
        self.assertEqual(result.source["final_url"], f"{origin}/final")
        self.assertLess(elapsed, 0.3)

    def test_real_redirect_chain_is_capped(self) -> None:
        class _RedirectLoopHandler(BaseRequestHandler):
            def handle(self) -> None:
                request = _receive_request_headers(self.request)
                target = request.split(b" ", 2)[1].decode("ascii")
                index = int(target.removeprefix("/"))
                self.request.sendall(
                    b"HTTP/1.1 302 Found\r\n"
                    + f"Location: /{index + 1}\r\n".encode()
                    + b"Content-Length: 0\r\n"
                    + b"Connection: close\r\n\r\n"
                )

        with _running_tcp_server(_RedirectLoopHandler) as origin:
            with self.assertRaisesRegex(RemoteFetchError, str(MAX_REDIRECTS)):
                fetch_changelog(
                    f"{origin}/0",
                    allow_http=True,
                    timeout=1.0,
                )

    def test_body_read_errors_do_not_expose_query_secrets(self) -> None:
        response = _FailingResponse(url="https://example.test/CHANGELOG.md?token=hunter2")
        with self.assertRaises(RemoteFetchError) as caught:
            fetch_changelog(
                "https://example.test/CHANGELOG.md?token=hunter2",
                transport=_Transport(response),
            )
        message = str(caught.exception)
        self.assertNotIn("hunter2", message)
        self.assertNotIn("token", message)
        self.assertTrue(response.closed)


class CliTests(unittest.TestCase):
    def test_default_profile_honors_environment(self) -> None:
        with patch.dict(os.environ, {"PH_CHANGELOG_PROFILE": "ph-eventing"}):
            importlib.reload(cli_module)
            args = cli_module.build_parser().parse_args(
                ["fetch", "https://example.test/CHANGELOG.md"]
            )
            self.assertEqual(args.profile, "ph-eventing")
        importlib.reload(cli_module)

    def test_valid_remote_changelog_emits_machine_json_and_exits_zero(self) -> None:
        stdout = io.StringIO()
        result = FetchResult(raw=VALID_RAW, source=_source())
        with (
            patch("ph_changelog_remote.cli.fetch_changelog", return_value=result),
            contextlib.redirect_stdout(stdout),
        ):
            status = main(["fetch", "https://example.test/CHANGELOG.md"])

        self.assertEqual(status, 0)
        machine = json.loads(stdout.getvalue())
        self.assertEqual(machine["format"], "ph-changelog-document")
        self.assertEqual(machine["source"], _source())
        self.assertTrue(machine["validation"]["valid"])

    def test_invalid_changelog_is_still_emitted_and_exits_one(self) -> None:
        stdout = io.StringIO()
        result = FetchResult(raw=b"not a changelog\n", source=_source())
        with (
            patch("ph_changelog_remote.cli.fetch_changelog", return_value=result),
            contextlib.redirect_stdout(stdout),
        ):
            status = main(["fetch", "https://example.test/CHANGELOG.md"])

        self.assertEqual(status, 1)
        machine = json.loads(stdout.getvalue())
        self.assertFalse(machine["validation"]["valid"])
        self.assertIsNone(machine["document"])

    def test_stdout_uses_explicit_utf8_bytes_when_buffer_is_available(self) -> None:
        stdout = _BinaryStdout()
        raw = VALID_RAW.replace(b"remote inspection", b"caf\xc3\xa9 inspection")
        result = FetchResult(raw=raw, source=_source())
        with (
            patch("ph_changelog_remote.cli.fetch_changelog", return_value=result),
            patch("ph_changelog_remote.cli.sys.stdout", stdout),
        ):
            status = main(["fetch", "https://example.test/CHANGELOG.md"])

        self.assertEqual(status, 0)
        decoded = stdout.buffer.getvalue().decode("utf-8")
        self.assertIn("caf\u00e9", decoded)
        json.loads(decoded)

    def test_file_output_uses_same_directory_atomic_replace(self) -> None:
        result = FetchResult(raw=VALID_RAW, source=_source())
        real_replace = os.replace
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "remote.json"
            with (
                patch("ph_changelog_remote.cli.fetch_changelog", return_value=result),
                patch("ph_changelog_remote.cli.os.replace", wraps=real_replace) as replace,
            ):
                status = main(
                    [
                        "fetch",
                        "https://example.test/CHANGELOG.md",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(status, 0)
            machine = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(machine["validation"]["valid"])
            temporary, target = replace.call_args.args
            self.assertEqual(Path(temporary).parent, output.parent)
            self.assertEqual(Path(target), output)

    def test_operational_failure_emits_no_json_and_preserves_output(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "remote.json"
            output.write_bytes(b"existing output")
            with (
                patch(
                    "ph_changelog_remote.cli.fetch_changelog",
                    side_effect=RemoteFetchError("network request failed"),
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                status = main(
                    [
                        "fetch",
                        "https://example.test/CHANGELOG.md",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(status, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("network request failed", stderr.getvalue())
            self.assertEqual(output.read_bytes(), b"existing output")

    def test_partial_content_is_operational_and_preserves_output(self) -> None:
        response = _Response(status=206, raw=VALID_RAW)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "remote.json"
            output.write_bytes(b"existing output")
            with (
                patch(
                    "ph_changelog_remote.fetch.HttpTransport",
                    return_value=_Transport(response),
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = main(
                    [
                        "fetch",
                        "https://example.test/CHANGELOG.md",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(status, 2)
            self.assertEqual(output.read_bytes(), b"existing output")

    def test_atomic_replace_failure_preserves_existing_output(self) -> None:
        result = FetchResult(raw=VALID_RAW, source=_source())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "remote.json"
            output.write_bytes(b"existing output")
            with (
                patch("ph_changelog_remote.cli.fetch_changelog", return_value=result),
                patch("ph_changelog_remote.cli.os.replace", side_effect=OSError("replace failed")),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = main(
                    [
                        "fetch",
                        "https://example.test/CHANGELOG.md",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(status, 2)
            self.assertEqual(output.read_bytes(), b"existing output")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    def test_cli_forwards_explicit_fetch_controls(self) -> None:
        result = FetchResult(raw=VALID_RAW, source=_source())
        with (
            patch("ph_changelog_remote.cli.fetch_changelog", return_value=result) as fetch,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = main(
                [
                    "--profile",
                    "ph-eventing",
                    "fetch",
                    "http://example.test/CHANGELOG.md",
                    "--timeout",
                    "3.5",
                    "--max-bytes",
                    "2048",
                    "--allow-http",
                ]
            )
        self.assertEqual(status, 0)
        fetch.assert_called_once_with(
            "http://example.test/CHANGELOG.md",
            timeout=3.5,
            max_bytes=2048,
            allow_http=True,
        )

    def test_cli_exposes_no_auth_or_insecure_transport_option(self) -> None:
        parser = build_parser()
        option_strings: set[str] = set()
        pending = [parser]
        while pending:
            current = pending.pop()
            for action in current._actions:
                option_strings.update(action.option_strings)
                choices = getattr(action, "choices", None)
                if isinstance(choices, dict):
                    pending.extend(choices.values())
        forbidden = {"--auth", "--header", "--token", "--insecure", "--no-verify"}
        self.assertEqual(option_strings & forbidden, set())


class DependencyBoundaryTests(unittest.TestCase):
    def test_remote_adapter_does_not_import_agent_package(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src" / "ph_changelog_remote"
        imported: set[str] = set()
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
        self.assertNotIn("ph_changelog_agent", imported)


if __name__ == "__main__":
    unittest.main()
