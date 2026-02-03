from __future__ import annotations

from typing import Any

import httpx

from app.utils.network import get_httpx_proxy


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    follow_redirects: bool = False,
    proxy: str | dict[str, str] | None = None,
) -> httpx.Response:
    effective_proxy = proxy if proxy is not None else get_httpx_proxy()

    try:
        return httpx.request(
            method,
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            trust_env=False,
            proxy=effective_proxy,
        )
    except Exception:
        if effective_proxy:
            return httpx.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                follow_redirects=follow_redirects,
                trust_env=False,
            )
        raise


def get_bytes(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    follow_redirects: bool = False,
    proxy: str | dict[str, str] | None = None,
) -> bytes:
    resp = request(
        "GET",
        url,
        params=params,
        headers=headers,
        timeout=timeout,
        follow_redirects=follow_redirects,
        proxy=proxy,
    )
    return resp.content


def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    follow_redirects: bool = False,
    proxy: str | dict[str, str] | None = None,
) -> Any:
    resp = request(
        "GET",
        url,
        params=params,
        headers=headers,
        timeout=timeout,
        follow_redirects=follow_redirects,
        proxy=proxy,
    )
    return resp.json()

