from urllib.parse import urlsplit, urlunsplit


def normalize_sdcpp_server_url(url: str) -> str:
    """Return a normalized HTTP(S) base URL for an external sd.cpp server.

    Raises:
        ValueError: If the URL is missing or unusable. Callers translate this
            into whatever error type fits their layer.
    """
    raw_url = (url or "").strip()
    if not raw_url:
        raise ValueError("Remote sd.cpp server URL is required.")

    parsed = urlsplit(raw_url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            "Remote sd.cpp server URL must be an absolute HTTP or HTTPS URL."
        )
    if parsed.username or parsed.password:
        raise ValueError("Remote sd.cpp server URL must not contain credentials.")
    # Stripping these silently would drop an auth token the user meant to send,
    # leaving unauthenticated requests and a puzzling rejection from the server.
    if parsed.query or parsed.fragment:
        raise ValueError(
            "Remote sd.cpp server URL must not contain a query string or fragment."
        )
    try:
        port = parsed.port
    except ValueError as e:
        raise ValueError(f"Remote sd.cpp server URL has an invalid port: {e}") from e
    if port == 0:
        raise ValueError("Remote sd.cpp server URL has an invalid port: 0.")

    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", "")
    )
