"""FICTIONAL feed examples: HTML snippets are data; XML DTDs are rejected."""
from types import SimpleNamespace

import pytest

from collectors import support


@pytest.mark.parametrize("snippet", [
    b"<![CDATA[FICTIONAL example: <!DOCTYPE html> <!ENTITY example>]]>",
    b"FICTIONAL example: &lt;!DOCTYPE html&gt;",
])
def test_feed_accepts_literal_html_declarations(monkeypatch, snippet):
    content = (b"<rss version='2.0'><channel><title>FICTIONAL</title><item>"
               b"<title>FICTIONAL article</title><description>" + snippet +
               b"</description></item></channel></rss>")
    monkeypatch.setattr(support.requests, "get", lambda *a, **k:
                        SimpleNamespace(content=content, raise_for_status=lambda: None))
    entries, elements = support.fetch_feed("https://fictional.example/feed")
    assert len(entries) == len(elements) == 1


@pytest.mark.parametrize("declaration", [
    b"<!DOCTYPE rss SYSTEM 'https://fictional.example/external.dtd'>",
    b"<!DOCTYPE rss [<!ENTITY fictional 'invented text'>]>",
])
def test_feed_rejects_actual_xml_dtd(monkeypatch, declaration):
    content = declaration + b"<rss><channel><title>FICTIONAL</title></channel></rss>"
    monkeypatch.setattr(support.requests, "get", lambda *a, **k:
                        SimpleNamespace(content=content, raise_for_status=lambda: None))
    with pytest.raises(support.SourceFailure, match="unsupported XML declarations"):
        support.fetch_feed("https://fictional.example/feed")
