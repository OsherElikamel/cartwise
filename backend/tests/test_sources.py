from app.ingestion.sources import latest, parse_file_name


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
