from __future__ import annotations
import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " "(KHTML, like Gecko) Chrome/124 Safari/537.36"

# Heuristisk regex för att hitta en publik API-bas i sidans HTML/JS.
API_GUESS_PATTERNS = [
    r"https://[\w.-]*azurewebsites\.net/[^\"']*?api[\w/\-]*",
    r"https://[\w.-]*sysav[\w.-]*/[^\"']*?api[\w/\-]*",
]

MUNICIPALITY_SLUG = {
    "kavlinge": "kavlinge",
    "lomma": "lomma",
    "svedala": "svedala",
}

BASE_PAGE = "https://www.sysav.se/privat/min-sophamtning/{slug}"


class DiscoveryError(Exception):
    pass


class QueryError(Exception):
    pass


@dataclass
class ContainerDate:
    label: str
    date: datetime | None


class SysavClient:
    def __init__(self, api_base: str | None = None, session: aiohttp.ClientSession | None = None):
        self._session = session or aiohttp.ClientSession(headers={"User-Agent": USER_AGENT})
        self._api_base = api_base.rstrip("/") if api_base else None

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _discover_api_base(self, municipality: str) -> str:
        if self._api_base:
            return self._api_base

        url = BASE_PAGE.format(slug=MUNICIPALITY_SLUG[municipality])
        async with self._session.get(url, timeout=20) as resp:
            html = await resp.text()
        # Försök hitta första troliga API-url i sidans html/js
        for pat in API_GUESS_PATTERNS:
            m = re.search(pat, html)
            if m:
                base = m.group(0)
                # kapa på "/api" om möjligt för att få bas
                parts = base.split("/api")
                guess = parts[0] + "/api"
                _LOGGER.debug("SYSAV guessed API base: %s", guess)
                self._api_base = guess
                return self._api_base
        raise DiscoveryError("Kunde inte auto-identifiera API-bas från SYSAV-sidan")

    async def async_validate(self, municipality: str, street: str, number: str, city: str) -> None:
        # Gör ett minimal-lookupsförsök, ignorerar resultat
        _ = await self.fetch_next(municipality, street, number, city)

    async def fetch_next(self, municipality: str, street: str, number: str, city: str) -> dict[str, ContainerDate]:
        api_base = await self._discover_api_base(municipality)

        # Strategi A: känd (inofficiell) sök-endpoint (GET med query)
        # Ex: .../api/waste/collection?municipality=...&street=...&number=...&city=...
        params = {
            "municipality": municipality,
            "street": street,
            "number": number,
            "city": city,
        }
        endpoints_try = [
            f"{api_base}/waste/collection",
            f"{api_base}/collection/next",
            f"{api_base}/waste/search",
        ]

        last_exc: Exception | None = None
        for endpoint in endpoints_try:
            try:
                async with self._session.get(endpoint, params=params, timeout=25) as resp:
                    if resp.status == 404:
                        continue
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    return self._parse_payload(data)
            except Exception as exc:
                last_exc = exc
                _LOGGER.debug("SYSAV endpoint try failed %s: %s", endpoint, exc)
                continue

        # Strategi B: POST med JSON-body mot \n        # .../api/waste/collection (varierar över tid)
        body = {
            "municipality": municipality,
            "street": street,
            "streetNumber": number,
            "city": city,
        }
        for endpoint in endpoints_try:
            try:
                async with self._session.post(endpoint, json=body, timeout=25) as resp:
                    if resp.status == 404:
                        continue
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    return self._parse_payload(data)
            except Exception as exc:
                last_exc = exc
                _LOGGER.debug("SYSAV POST endpoint try failed %s: %s", endpoint, exc)
                continue

        raise QueryError(str(last_exc) if last_exc else "Ingen kompatibel endpoint hittad")

    def _parse_payload(self, data: Any) -> dict[str, ContainerDate]:
        """
        Försöker känna igen några sannolika JSON-format. Vi letar efter poster med
        namn/etikett och datum (nästa tömning). Stödjer flera nycklar.
        """
        results: dict[str, ContainerDate] = {}

        def to_dt(val: str | None):
            if not val:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    pass
            return None

        items = []
        if isinstance(data, dict):
            # vanliga fält
            if "containers" in data and isinstance(data["containers"], list):
                items = data["containers"]
            elif "result" in data and isinstance(data["result"], list):
                items = data["result"]
            elif "data" in data and isinstance(data["data"], list):
                items = data["data"]
        elif isinstance(data, list):
            items = data

        for it in items:
            label = it.get("label") or it.get("name") or it.get("container") or it.get("type") or ""
            # Datumfält att prova
            dt = (
                it.get("next")
                or it.get("nextEmptying")
                or it.get("next_collection")
                or it.get("nextDate")
                or it.get("date")
                or None
            )
            results[label] = ContainerDate(label=label, date=to_dt(dt) if isinstance(dt, str) else None)

        return results
