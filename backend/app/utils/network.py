from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from app.config import settings


def _normalize_proxy(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _rewrite_localhost(proxy: str) -> str:
    try:
        parts = urlsplit(proxy)
        hostname = parts.hostname
        if hostname not in {"localhost", "127.0.0.1"}:
            return proxy
        netloc = parts.netloc.replace(hostname, "host.docker.internal", 1)
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return proxy


def get_httpx_proxy() -> str | dict[str, str] | None:
    http_proxy = _normalize_proxy(settings.HTTP_PROXY)
    https_proxy = _normalize_proxy(settings.HTTPS_PROXY)

    http_proxy = _rewrite_localhost(http_proxy) if http_proxy else None
    https_proxy = _rewrite_localhost(https_proxy) if https_proxy else None

    if http_proxy and https_proxy:
        return {"http://": http_proxy, "https://": https_proxy}

    proxy = http_proxy or https_proxy
    if not proxy:
        return None

    return {"http://": proxy, "https://": proxy}

