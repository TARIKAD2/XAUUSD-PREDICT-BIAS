from app.collectors.news import normalize_rss

def test_rss_normalization_is_evidence_bearing():
    xml=b"<rss><channel><item><title>Gold rallies as CPI eases</title><description>Markets react.</description><link>https://example.com/story</link><pubDate>Mon, 01 Jan 2026 12:00:00 GMT</pubDate></item></channel></rss>"
    item=normalize_rss(xml,"fixture")[0]
    assert item.category.value=="macro"
    assert item.importance.value=="high"
    assert item.symbols[0].value=="XAUUSD"
    assert item.impacts[0].rationale