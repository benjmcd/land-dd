from __future__ import annotations

from app.api import ui_shared
from app.api.ui_shared import error_page


def test_page_head_escapes_title_supports_css_and_refresh_meta() -> None:
    page_head = getattr(ui_shared, "page_head", None)

    assert callable(page_head)
    head = page_head(
        "Run <Status>",
        css=".flag { color: red; }",
        refresh_url="/ui/next?x=<bad>&y='quoted'",
    )

    assert head.startswith("<head><meta charset='UTF-8'>")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in head
    assert "<title>Run &lt;Status&gt;</title>" in head
    assert (
        "<meta http-equiv='refresh' "
        "content='1;url=/ui/next?x=&lt;bad&gt;&amp;y=&#x27;quoted&#x27;'>"
    ) in head
    assert "<style>.flag { color: red; }</style>" in head
    assert head.endswith("</head>")


def test_error_page_escapes_content_and_includes_viewport_meta() -> None:
    response = error_page(
        "Bad <Title>",
        'Message with <script> & "quotes"',
        "/ui/back?next=<bad>&name='quoted'",
        418,
    )

    assert response.status_code == 418
    body = bytes(response.body).decode()
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in body
    assert "Bad &lt;Title&gt;" in body
    assert "Message with &lt;script&gt; &amp; &quot;quotes&quot;" in body
    assert "href='/ui/back?next=&lt;bad&gt;&amp;name=&#x27;quoted&#x27;'" in body
    assert "<script>" not in body
