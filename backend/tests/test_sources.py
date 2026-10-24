import httpx
import pytest

from app.core.errors import UpstreamError
from app.ingestion.sources import ShufersalSource, latest, parse_file_name


def test_parse_file_name_reads_store_and_timestamp():
    remote = parse_file_name("PriceFull7290027600007-002-092-20261019-030000.gz", "url")
    assert (remote.kind, remote.store_code, remote.timestamp) == ("PriceFull", "92", "20261019030000")


def test_parse_file_name_accepts_short_time_and_storeless_files():
    # Shufersal's Stores file uses a 3-digit time part and has no store segment.
    remote = parse_file_name("Stores7290027600007-000-20261019-020.gz", "url")
    assert remote.kind == "Stores"
    assert remote.store_code is None


def test_parse_file_name_rejects_unknown_files():
    assert parse_file_name("Price7290027600007-001-001-20261019-0300.gz", "url") is None
    assert parse_file_name("readme.txt", "url") is None


def test_latest_picks_newest_file_for_the_store():
    files = [
        parse_file_name("PriceFull7290058140886-001-001-20261019-001002.gz", "a"),
        parse_file_name("PriceFull7290058140886-001-001-20261019-121501.gz", "b"),
        parse_file_name("PriceFull7290058140886-001-002-20261020-000000.gz", "c"),
    ]
    assert latest(files, "PriceFull", "1").url == "b"
    assert latest(files, "PromoFull", "1") is None


SHUFERSAL_PAGE = '<a href="https://pricesprodpublic.blob.core.windows.net/price/PriceFull7290027600007-002-092-20261024-030840.gz?sv=1&amp;sig=x">'


def _shufersal(responses):
    """A ShufersalSource whose requests get `responses` in order (an exception is raised)."""
    calls = []

    def handler(request):
        calls.append(request)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    sleeps = []
    source = ShufersalSource(sleep=sleeps.append)
    source.client = httpx.Client(transport=httpx.MockTransport(handler))
    return source, calls, sleeps


def test_shufersal_retries_a_stalled_file_list():
    source, calls, sleeps = _shufersal([httpx.ReadTimeout("stalled"), httpx.Response(200, text=SHUFERSAL_PAGE)])
    files = source.list_files("PriceFull", "92")
    assert [f.store_code for f in files] == ["92"]
    assert len(calls) == 2
    assert sleeps == [10]


def test_shufersal_gives_up_and_skips_the_rest_of_the_run():
    stalls = [httpx.ReadTimeout("stalled") for _ in range(3)]
    source, calls, sleeps = _shufersal(stalls)
    with pytest.raises(UpstreamError, match="after 3 tries"):
        source.list_files("PriceFull", "92")
    # The next branch doesn't wait through the same outage again.
    with pytest.raises(UpstreamError, match="skipped"):
        source.list_files("PriceFull", "205")
    assert len(calls) == 3
    assert sleeps == [10, 30]


def test_shufersal_does_not_retry_a_client_error():
    source, calls, sleeps = _shufersal([httpx.Response(404)])
    with pytest.raises(UpstreamError):
        source.list_files("PriceFull", "92")
    assert len(calls) == 1
    assert sleeps == []
