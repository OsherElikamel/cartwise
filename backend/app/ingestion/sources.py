"""Where each chain publishes its files.

Two portal types cover the four v1 chains:
- Shufersal runs its own site that links to signed Azure blob URLs.
- Rami Levy, Yohananof and Osher Ad share url.publishedprices.co.il,
  which needs a per-chain login (public username, empty password).

Both expose the same interface, so the pipeline never cares which is which.
"""

import html
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.errors import UpstreamError
from app.ingestion.parsers import normalize_store_code

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(60.0, connect=15.0)

# PriceFull7290027600007-001-001-20261019-030000.gz
# Stores7290058140886-000-20261019-050500.xml
FILE_NAME_RE = re.compile(
    r"^(?P<kind>PriceFull|PromoFull|Stores)(?P<chain>\d{13})-(?P<sub>\d+)"
    r"(?:-(?P<store>\d+))?-(?P<date>\d{8})-?(?P<time>\d{3,6})\.(?:gz|xml)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RemoteFile:
    name: str
    url: str
    kind: str
    store_code: str | None
    timestamp: str


def parse_file_name(name: str, url: str) -> RemoteFile | None:
    match = FILE_NAME_RE.match(name)
    if not match:
        return None
    store = match.group("store")
    kind = {"pricefull": "PriceFull", "promofull": "PromoFull", "stores": "Stores"}[match.group("kind").lower()]
    return RemoteFile(
        name=name,
        url=url,
        kind=kind,
        store_code=normalize_store_code(store) if store else None,
        timestamp=match.group("date") + match.group("time").ljust(6, "0"),
    )


def latest(files: list[RemoteFile], kind: str, store_code: str | None = None) -> RemoteFile | None:
    matching = [f for f in files if f.kind == kind and (store_code is None or f.store_code == store_code)]
    return max(matching, key=lambda f: f.timestamp, default=None)


class Source(Protocol):
    def list_files(self, kind: str, store_code: str | None = None) -> list[RemoteFile]: ...

    def download(self, remote: RemoteFile) -> bytes: ...


class ShufersalSource:
    BASE_URL = "https://prices.shufersal.co.il/FileObject/UpdateCategory"
    CATEGORIES = {"PriceFull": 2, "PromoFull": 4, "Stores": 5}
    # From abroad (the nightly job runs on US servers) the site answers in seconds on
    # most days and stalls past the timeout on others, so a stall gets two more tries.
    RETRY_DELAYS = (10, 30)

    def __init__(self, sleep: Callable[[float], None] = time.sleep) -> None:
        self.client = httpx.Client(timeout=TIMEOUT, follow_redirects=True)
        self._sleep = sleep
        # Once every try has failed, the rest of the run skips the site instead of
        # spending minutes per branch on the same outage.
        self._unreachable = False

    def _get(self, url: str, what: str, params: dict | None = None) -> httpx.Response:
        if self._unreachable:
            raise UpstreamError(f"{what} skipped: Shufersal was unreachable earlier in this run")
        delays = list(self.RETRY_DELAYS)
        while True:
            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                retryable = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500
                )
                if not retryable:
                    raise UpstreamError(f"{what} failed: {exc}") from exc
                if not delays:
                    self._unreachable = True
                    raise UpstreamError(f"{what} failed after {len(self.RETRY_DELAYS) + 1} tries: {exc}") from exc
                delay = delays.pop(0)
                logger.warning("%s failed (%s); trying again in %ds", what, exc, delay)
                self._sleep(delay)

    def list_files(self, kind: str, store_code: str | None = None) -> list[RemoteFile]:
        params = {"catID": self.CATEGORIES[kind], "storeId": store_code or 0, "page": 1}
        response = self._get(self.BASE_URL, "Shufersal file list", params=params)

        files = []
        for raw_url in re.findall(r'href="(https://pricesprodpublic[^"]+)"', response.text):
            url = html.unescape(raw_url)
            name = url.split("?")[0].rsplit("/", 1)[-1]
            remote = parse_file_name(name, url)
            if remote and (store_code is None or remote.store_code == store_code):
                files.append(remote)
        return files

    def download(self, remote: RemoteFile) -> bytes:
        return self._get(remote.url, f"Shufersal download of {remote.name}").content


class PublishedPricesSource:
    BASE_URL = "https://url.publishedprices.co.il"
    CSRF_RE = re.compile(r'name="csrftoken"\s+content="([^"]+)"')

    def __init__(self, username: str) -> None:
        self.username = username
        self.client = httpx.Client(base_url=self.BASE_URL, timeout=TIMEOUT, follow_redirects=True)
        self._logged_in = False

    def _csrf(self, path: str) -> str:
        response = self.client.get(path)
        response.raise_for_status()
        match = self.CSRF_RE.search(response.text)
        if not match:
            raise UpstreamError(f"No CSRF token on {path} for {self.username}")
        return match.group(1)

    def _login(self) -> None:
        if self._logged_in:
            return
        try:
            token = self._csrf("/login")
            response = self.client.post(
                "/login/user",
                data={"r": "", "username": self.username, "password": "", "Submit": "Sign in", "csrftoken": token},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UpstreamError(f"publishedprices login failed for {self.username}: {exc}") from exc
        if "/login" in str(response.url):
            raise UpstreamError(f"publishedprices rejected the login for {self.username}")
        self._logged_in = True

    def list_files(self, kind: str, store_code: str | None = None) -> list[RemoteFile]:
        self._login()
        try:
            token = self._csrf("/file")
            response = self.client.post(
                "/file/json/dir",
                data={
                    "sEcho": 1, "iColumns": 5, "iDisplayStart": 0, "iDisplayLength": 100000,
                    "sSearch": kind, "cd": "/", "csrftoken": token,
                },
            )
            response.raise_for_status()
            rows = response.json().get("aaData", [])
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError(f"publishedprices file list failed for {self.username}: {exc}") from exc

        files = []
        for row in rows:
            remote = parse_file_name(row.get("fname", ""), f"/file/d/{row.get('fname', '')}")
            if remote and (store_code is None or remote.store_code == store_code):
                files.append(remote)
        return files

    def download(self, remote: RemoteFile) -> bytes:
        self._login()
        try:
            response = self.client.get(remote.url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UpstreamError(f"publishedprices download failed for {remote.name}: {exc}") from exc
        return response.content
