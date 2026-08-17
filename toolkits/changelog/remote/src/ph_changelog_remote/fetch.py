"""Constrained HTTP retrieval with a mockable transport boundary."""

from __future__ import annotations

import codecs
import http.client
import math
import queue
import re
import socket
import ssl
import threading
import time
from contextlib import closing
from dataclasses import dataclass
from email.message import Message
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit
from urllib.request import Request

DEFAULT_MAX_BYTES = 4_194_304
DEFAULT_TIMEOUT = 10.0
MAX_REDIRECTS = 5
USER_AGENT = "ph-changelog-remote/0.1.0"
ACCEPT = (
    "text/markdown, text/plain;q=0.9, application/markdown;q=0.8, "
    "text/x-markdown;q=0.8, application/octet-stream;q=0.5"
)
SUPPORTED_MEDIA_TYPES = frozenset(
    {
        "application/markdown",
        "application/octet-stream",
        "text/markdown",
        "text/plain",
        "text/x-markdown",
    }
)

_ENCODED_CONTROL = re.compile(r"%(?:[01][0-9a-f]|7f)", re.IGNORECASE)
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_DNS_SLOTS = threading.BoundedSemaphore(value=4)


class RemoteFetchError(Exception):
    """A query-redacted, user-facing remote retrieval failure."""


class Transport(Protocol):
    """Small seam used to test request and response handling without a network."""

    def open(self, request: Request, *, timeout: float) -> Any: ...


@dataclass(frozen=True, slots=True)
class FetchResult:
    raw: bytes
    source: dict[str, object]


def _has_forbidden_characters(url: str) -> bool:
    return any(
        character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url
    )


def _validate_url(url: str, *, allow_http: bool) -> SplitResult:
    if not isinstance(url, str) or not url:
        raise RemoteFetchError("remote URL must be a non-empty string")
    if _has_forbidden_characters(url) or _ENCODED_CONTROL.search(url):
        raise RemoteFetchError("remote URL must not contain whitespace or control characters")
    if "#" in url:
        raise RemoteFetchError("remote URL fragments are not allowed")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port  # Validate malformed and out-of-range ports.
    except ValueError as error:
        raise RemoteFetchError("remote URL is malformed") from error

    if parsed.scheme not in {"https", "http"}:
        raise RemoteFetchError("remote URL scheme must be HTTPS")
    if parsed.scheme == "http" and not allow_http:
        raise RemoteFetchError("plain HTTP requires --allow-http")
    if not hostname:
        raise RemoteFetchError("remote URL must include a host")
    if port == 0:
        raise RemoteFetchError("remote URL port must be between 1 and 65535")
    if parsed.username is not None or parsed.password is not None:
        raise RemoteFetchError("remote URL credentials are not allowed")
    return parsed


def _sanitize_url(url: str) -> str:
    """Remove query, fragment, and any user information from a display URL."""

    try:
        parsed = urlsplit(url)
    except (TypeError, ValueError):
        return "<invalid URL>"
    netloc = parsed.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", "")) or "<invalid URL>"


def _check_deadline(deadline: float, *, display_url: str) -> None:
    if time.monotonic() >= deadline:
        raise RemoteFetchError(f"remote request exceeded its deadline for {display_url}")


def _resolve_host(
    hostname: str,
    port: int,
    *,
    deadline: float,
    display_url: str,
) -> list[tuple[Any, ...]]:
    """Resolve without letting a synchronous OS resolver block the caller."""

    remaining = deadline - time.monotonic()
    if remaining <= 0 or not _DNS_SLOTS.acquire(timeout=remaining):
        raise RemoteFetchError(f"remote request exceeded its deadline for {display_url}")

    result_queue: queue.Queue[tuple[bool, object]] = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            result: tuple[bool, object] = (
                True,
                socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM),
            )
        except Exception as error:
            result = (False, error)
        finally:
            _DNS_SLOTS.release()
        result_queue.put_nowait(result)

    resolver = threading.Thread(target=resolve, name="ph-changelog-dns", daemon=True)
    resolver.start()
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RemoteFetchError(f"remote request exceeded its deadline for {display_url}")
    try:
        succeeded, result = result_queue.get(timeout=remaining)
    except queue.Empty:
        raise RemoteFetchError(f"remote request exceeded its deadline for {display_url}") from None
    if not succeeded:
        assert isinstance(result, Exception)
        raise result
    assert isinstance(result, list)
    return result


def _redirect_url(current_url: str, location: str, *, allow_http: bool) -> str:
    if not isinstance(location, str) or not location:
        raise RemoteFetchError("redirect Location must be a non-empty string")
    absolute = urljoin(current_url, location)
    previous = _validate_url(current_url, allow_http=True)
    target = _validate_url(absolute, allow_http=True)
    if previous.scheme == "https" and target.scheme == "http":
        raise RemoteFetchError("HTTPS redirects may not downgrade to HTTP")
    if target.scheme == "http" and not allow_http:
        raise RemoteFetchError("redirect to plain HTTP requires --allow-http")
    return absolute


def _resource_socket(resource: Any) -> Any | None:
    if isinstance(resource, socket.socket):
        return resource
    direct = getattr(resource, "sock", None)
    if direct is not None:
        return direct
    stream = getattr(resource, "fp", None)
    raw_stream = getattr(stream, "raw", None)
    return getattr(raw_stream, "_sock", None)


def _abort_resources(resources: tuple[Any, ...]) -> None:
    seen_sockets: set[int] = set()
    for resource in resources:
        active_socket = _resource_socket(resource)
        if active_socket is None or id(active_socket) in seen_sockets:
            continue
        seen_sockets.add(id(active_socket))
        try:
            active_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            active_socket.close()
        except OSError:
            pass
    for resource in reversed(resources):
        try:
            resource.close()
        except Exception:
            pass


class _DeadlineWatchdog:
    """Abort the active connection at one absolute monotonic deadline."""

    def __init__(self, deadline: float) -> None:
        self._lock = threading.Lock()
        self._resources: tuple[Any, ...] = ()
        self._expired = False
        self._cancelled = False
        self._timer = threading.Timer(max(0.0, deadline - time.monotonic()), self._expire)
        self._timer.daemon = True
        self._timer.start()

    @property
    def expired(self) -> bool:
        with self._lock:
            return self._expired

    def replace(self, *resources: Any) -> None:
        with self._lock:
            self._resources = resources
            expired = self._expired
        if expired:
            _abort_resources(resources)

    def _expire(self) -> None:
        with self._lock:
            if self._cancelled:
                return
            self._expired = True
            resources = self._resources
        _abort_resources(resources)

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            self._resources = ()
        self._timer.cancel()

    def abort(self) -> None:
        with self._lock:
            self._cancelled = True
            resources = self._resources
            self._resources = ()
        self._timer.cancel()
        _abort_resources(resources)


class _ManagedResponse:
    def __init__(
        self,
        response: http.client.HTTPResponse,
        connection: http.client.HTTPConnection,
        url: str,
        watchdog: _DeadlineWatchdog,
        deadline: float,
    ) -> None:
        self._response = response
        self._connection = connection
        self._url = url
        self._watchdog = watchdog
        self._deadline = deadline
        self._closed = False

    @property
    def status(self) -> int:
        return self._response.status

    @property
    def headers(self) -> Any:
        return self._response.headers

    @property
    def fp(self) -> Any:
        return self._response.fp

    def geturl(self) -> str:
        return self._url

    def getcode(self) -> int:
        return self.status

    def _read(self, method: str, size: int) -> bytes:
        try:
            return getattr(self._response, method)(size)
        except Exception:
            if self._watchdog.expired or time.monotonic() >= self._deadline:
                raise RemoteFetchError(
                    f"remote request exceeded its deadline for {_sanitize_url(self._url)}"
                ) from None
            raise

    def read(self, size: int = -1) -> bytes:
        return self._read("read", size)

    def read1(self, size: int = -1) -> bytes:
        return self._read("read1", size)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._watchdog.cancel()
        try:
            self._response.close()
        finally:
            self._connection.close()


class HttpTransport:
    """Verified-TLS stdlib transport with manual, non-draining redirects."""

    def __init__(self, *, allow_http: bool, deadline: float) -> None:
        self._allow_http = allow_http
        self._deadline = deadline
        self._tls_context = ssl.create_default_context()
        if ssl.HAS_ALPN:
            self._tls_context.set_alpn_protocols(["http/1.1"])

    def _connected_connection(
        self,
        parsed: SplitResult,
        *,
        timeout: float,
        watchdog: _DeadlineWatchdog,
        display_url: str,
    ) -> http.client.HTTPConnection:
        assert parsed.hostname is not None
        if parsed.scheme == "https":
            connection: http.client.HTTPConnection = http.client.HTTPSConnection(
                parsed.hostname,
                parsed.port,
                timeout=timeout,
                context=self._tls_context,
            )
        else:
            connection = http.client.HTTPConnection(
                parsed.hostname,
                parsed.port,
                timeout=timeout,
            )
        watchdog.replace(connection)

        port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
        addresses = _resolve_host(
            parsed.hostname,
            port,
            deadline=self._deadline,
            display_url=display_url,
        )
        last_error: OSError | None = None
        for family, socket_type, protocol, _, socket_address in addresses:
            _check_deadline(self._deadline, display_url=display_url)
            candidate: socket.socket | None = None
            try:
                candidate = socket.socket(family, socket_type, protocol)
                watchdog.replace(connection, candidate)
                candidate.settimeout(self._deadline - time.monotonic())
                candidate.connect(socket_address)
                _check_deadline(self._deadline, display_url=display_url)
                if parsed.scheme == "https":
                    candidate.settimeout(self._deadline - time.monotonic())
                    active_socket = self._tls_context.wrap_socket(
                        candidate,
                        server_hostname=parsed.hostname,
                    )
                else:
                    active_socket = candidate
            except OSError as error:
                last_error = error
                if candidate is not None:
                    try:
                        candidate.close()
                    except OSError:
                        pass
                continue

            connection.sock = active_socket
            watchdog.replace(connection, active_socket)
            _check_deadline(self._deadline, display_url=display_url)
            return connection

        if last_error is not None:
            raise last_error
        raise OSError("DNS resolution returned no stream addresses")

    def open(self, request: Request, *, timeout: float) -> Any:
        if request.get_method() != "GET":
            raise RemoteFetchError("remote transport supports GET only")

        current_url = request.full_url
        headers = dict(request.header_items())
        watchdog = _DeadlineWatchdog(self._deadline)
        try:
            for redirect_count in range(MAX_REDIRECTS + 1):
                parsed = _validate_url(current_url, allow_http=self._allow_http)
                display_url = _sanitize_url(current_url)
                _check_deadline(self._deadline, display_url=display_url)
                remaining = min(timeout, self._deadline - time.monotonic())
                if remaining <= 0:
                    raise RemoteFetchError(
                        f"remote request exceeded its deadline for {display_url}"
                    )

                connection = self._connected_connection(
                    parsed,
                    timeout=remaining,
                    watchdog=watchdog,
                    display_url=display_url,
                )
                target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
                connection.request("GET", target, headers=headers)
                response = connection.getresponse()
                watchdog.replace(connection, response)
                if watchdog.expired or time.monotonic() >= self._deadline:
                    raise RemoteFetchError(
                        f"remote request exceeded its deadline for {display_url}"
                    )

                if response.status not in _REDIRECT_STATUSES:
                    return _ManagedResponse(
                        response,
                        connection,
                        current_url,
                        watchdog,
                        self._deadline,
                    )

                location = response.headers.get("Location")
                if location is None:
                    return _ManagedResponse(
                        response,
                        connection,
                        current_url,
                        watchdog,
                        self._deadline,
                    )
                if redirect_count >= MAX_REDIRECTS:
                    raise RemoteFetchError(f"remote request exceeded {MAX_REDIRECTS} redirects")

                next_url = _redirect_url(
                    current_url,
                    location,
                    allow_http=self._allow_http,
                )
                # Redirect bodies are irrelevant to a snapshot fetch. Closing
                # instead of draining them prevents an unbounded side channel.
                response.close()
                connection.close()
                watchdog.replace()
                current_url = next_url
        except Exception as error:
            expired = watchdog.expired or time.monotonic() >= self._deadline
            watchdog.abort()
            if expired and not isinstance(error, RemoteFetchError):
                raise RemoteFetchError(
                    f"remote request exceeded its deadline for {_sanitize_url(current_url)}"
                ) from None
            raise

        raise AssertionError("redirect loop did not return or fail")


def _header_values(headers: Any, name: str) -> list[str]:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        values = get_all(name)
        if values is None:
            return []
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise RemoteFetchError(f"response {name} header is not textual")
        return values

    value = headers.get(name)
    if value is None:
        value = headers.get(name.lower())
    if value is None:
        return []
    if not isinstance(value, str):
        raise RemoteFetchError(f"response {name} header is not textual")
    return [value]


def _header(headers: Any, name: str) -> str | None:
    values = _header_values(headers, name)
    if len(values) > 1:
        raise RemoteFetchError(f"response {name} header must not be repeated")
    return values[0] if values else None


def _content_type(headers: Any, *, display_url: str) -> str | None:
    raw_value = _header(headers, "Content-Type")
    if raw_value is None:
        return None

    media_type = raw_value.split(";", 1)[0].strip().lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise RemoteFetchError(f"unsupported response media type {media_type!r} from {display_url}")

    message = Message()
    message["Content-Type"] = raw_value
    for name, value in message.get_params(header="content-type", failobj=[])[1:]:
        if name.lower() != "charset":
            continue
        try:
            normalized = codecs.lookup(value).name
        except (LookupError, TypeError) as error:
            raise RemoteFetchError(
                f"response declares an invalid charset from {display_url}"
            ) from error
        if normalized != "utf-8":
            raise RemoteFetchError(
                f"response charset must be UTF-8, not {value!r}, from {display_url}"
            )
    return media_type


def _content_length(headers: Any, *, max_bytes: int, display_url: str) -> int | None:
    value = _header(headers, "Content-Length")
    if value is None:
        return None
    stripped = value.strip()
    if not stripped.isascii() or not stripped.isdigit():
        raise RemoteFetchError(f"response has an invalid Content-Length from {display_url}")
    parsed = int(stripped)
    if parsed > max_bytes:
        raise RemoteFetchError(f"response exceeds the {max_bytes}-byte limit from {display_url}")
    return parsed


def _read_bounded(
    response: Any,
    *,
    max_bytes: int,
    display_url: str,
    deadline: float,
    expected_length: int | None,
) -> bytes:
    chunks: list[bytes] = []
    remaining = max_bytes
    while True:
        _check_deadline(deadline, display_url=display_url)
        remaining_time = deadline - time.monotonic()

        # ``HTTPResponse.read(size)`` may wait for the full requested size while
        # a peer continuously drips bytes. ``read1`` performs at most one
        # underlying receive, which lets us re-check the deadline between
        # packets. Also narrow the live socket timeout so a stalled receive
        # cannot extend past the remaining overall deadline.
        stream = getattr(response, "fp", None)
        raw_stream = getattr(stream, "raw", None)
        response_socket = getattr(raw_stream, "_sock", None)
        set_timeout = getattr(response_socket, "settimeout", None)
        if callable(set_timeout):
            set_timeout(remaining_time)

        read_once = getattr(response, "read1", None)
        if not callable(read_once):
            read_once = response.read
        try:
            chunk = read_once(min(65_536, remaining + 1))
        except TimeoutError:
            raise RemoteFetchError(
                f"remote request exceeded its deadline for {display_url}"
            ) from None
        _check_deadline(deadline, display_url=display_url)
        if not isinstance(chunk, bytes):
            raise RemoteFetchError(f"response body is not bytes from {display_url}")
        if len(chunk) > remaining:
            raise RemoteFetchError(
                f"response exceeds the {max_bytes}-byte limit from {display_url}"
            )
        if not chunk:
            received = max_bytes - remaining
            if expected_length is not None and received != expected_length:
                raise RemoteFetchError(
                    f"response ended after {received} bytes; expected "
                    f"{expected_length} from {display_url}"
                )
            return b"".join(chunks)
        chunks.append(chunk)
        remaining -= len(chunk)


def _consume_response(
    response: Any,
    *,
    requested: SplitResult,
    requested_display: str,
    allow_http: bool,
    max_bytes: int,
    deadline: float,
) -> FetchResult:
    with closing(response):
        _check_deadline(deadline, display_url=requested_display)
        final_url = response.geturl()
        if not isinstance(final_url, str):
            raise RemoteFetchError("response final URL is not textual")
        final = _validate_url(final_url, allow_http=allow_http)
        if requested.scheme == "https" and final.scheme == "http":
            raise RemoteFetchError("HTTPS requests may not finish on plain HTTP")
        final_display = _sanitize_url(final_url)

        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()
        if isinstance(status, bool) or not isinstance(status, int):
            raise RemoteFetchError(f"response status is invalid from {final_display}")
        if status != 200:
            raise RemoteFetchError(f"HTTP status {status} fetching {final_display}")

        headers = response.headers
        if _header_values(headers, "Content-Range"):
            raise RemoteFetchError(
                f"partial Content-Range responses are unsupported from {final_display}"
            )
        content_encodings = _header_values(headers, "Content-Encoding")
        if len(content_encodings) > 1 or (
            content_encodings and content_encodings[0].strip().lower() != "identity"
        ):
            raise RemoteFetchError(
                f"compressed or encoded responses are unsupported from {final_display}"
            )
        transfer_encodings = _header_values(headers, "Transfer-Encoding")
        if len(transfer_encodings) > 1 or (
            transfer_encodings and transfer_encodings[0].strip().lower() != "chunked"
        ):
            raise RemoteFetchError(f"unsupported response Transfer-Encoding from {final_display}")
        media_type = _content_type(headers, display_url=final_display)
        expected_length = _content_length(
            headers,
            max_bytes=max_bytes,
            display_url=final_display,
        )
        if transfer_encodings and expected_length is not None:
            raise RemoteFetchError(
                f"response must not combine Transfer-Encoding and Content-Length "
                f"from {final_display}"
            )
        raw = _read_bounded(
            response,
            max_bytes=max_bytes,
            display_url=final_display,
            deadline=deadline,
            expected_length=expected_length,
        )

        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RemoteFetchError(f"response is not strict UTF-8 from {final_display}") from error

        source: dict[str, object] = {
            "kind": "http",
            "requested_url": requested_display,
            "final_url": final_display,
            "query_redacted": bool(requested.query or final.query),
            "status": status,
            "content_type": media_type,
            "etag": _header(headers, "ETag"),
            "last_modified": _header(headers, "Last-Modified"),
        }
        return FetchResult(raw=raw, source=source)


def fetch_changelog(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    allow_http: bool = False,
    transport: Transport | None = None,
) -> FetchResult:
    """Fetch one changelog snapshot and return exact bytes plus closed metadata."""

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise RemoteFetchError("timeout must be a positive finite number")
    timeout = float(timeout)
    if not math.isfinite(timeout) or timeout <= 0:
        raise RemoteFetchError("timeout must be a positive finite number")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise RemoteFetchError("max-bytes must be a positive integer")
    if type(allow_http) is not bool:
        raise RemoteFetchError("allow_http must be a boolean")

    requested = _validate_url(url, allow_http=allow_http)
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": ACCEPT,
            "Accept-Encoding": "identity",
        },
    )
    requested_display = _sanitize_url(url)
    deadline = time.monotonic() + timeout
    active_transport = transport or HttpTransport(
        allow_http=allow_http,
        deadline=deadline,
    )
    try:
        remaining_timeout = deadline - time.monotonic()
        if remaining_timeout <= 0:
            raise RemoteFetchError(f"remote request exceeded its deadline for {requested_display}")
        response = active_transport.open(request, timeout=remaining_timeout)
    except RemoteFetchError:
        raise
    except HTTPError as error:
        display_url = _sanitize_url(error.url) if error.url else requested_display
        try:
            error.close()
        except Exception:
            pass
        raise RemoteFetchError(f"HTTP status {error.code} fetching {display_url}") from None
    except URLError:
        raise RemoteFetchError(f"network request failed for {requested_display}") from None
    except TimeoutError:
        raise RemoteFetchError(f"network request timed out for {requested_display}") from None
    except Exception:
        raise RemoteFetchError(f"network request failed for {requested_display}") from None

    try:
        return _consume_response(
            response,
            requested=requested,
            requested_display=requested_display,
            allow_http=allow_http,
            max_bytes=max_bytes,
            deadline=deadline,
        )
    except RemoteFetchError:
        raise
    except TimeoutError:
        raise RemoteFetchError(f"network request timed out for {requested_display}") from None
    except Exception:
        raise RemoteFetchError(f"response processing failed for {requested_display}") from None
