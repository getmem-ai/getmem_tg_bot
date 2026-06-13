from app.bot.formatting import to_telegram_html


def test_bold_italic_strike() -> None:
    assert to_telegram_html("**hi**") == "<b>hi</b>"
    assert to_telegram_html("_hi_") == "<i>hi</i>"
    assert to_telegram_html("~~no~~") == "<s>no</s>"


def test_inline_and_block_code() -> None:
    assert to_telegram_html("use `x = 1`") == "use <code>x = 1</code>"
    out = to_telegram_html("```python\nprint(1)\n```")
    assert out == "<pre>print(1)</pre>"


def test_headings_become_bold() -> None:
    assert to_telegram_html("### Title") == "<b>Title</b>"


def test_bullets_and_numbered() -> None:
    out = to_telegram_html("- one\n- two")
    assert out == "• one\n• two"
    assert to_telegram_html("1. first") == "1. first"


def test_links() -> None:
    assert (
        to_telegram_html("[GetMem](https://getmem.ai)")
        == '<a href="https://getmem.ai">GetMem</a>'
    )


def test_html_is_escaped() -> None:
    # Stray angle brackets/ampersands must be escaped, never break parsing.
    out = to_telegram_html("a < b & c > d")
    assert "&lt;" in out and "&amp;" in out and "&gt;" in out
    assert "<b" not in out  # no accidental tags


def test_table_renders_without_pipes_or_markdown() -> None:
    md = (
        "| Type | Rod | Length |\n"
        "|------|-----|--------|\n"
        "| **Freshwater** | Spinning | 2.1m |\n"
        "| Saltwater | Surf | 3.0m |\n"
    )
    out = to_telegram_html(md)
    assert "|" not in out
    assert "---" not in out
    assert "**" not in out
    assert "<b>Freshwater</b>" in out
    assert "Rod: Spinning" in out
    assert "Length: 2.1m" in out


def test_no_leftover_markdown_markers_on_complex_input() -> None:
    md = "## Heading\n\nSome **bold** and a list:\n- item `code`\n\n| A | B |\n|---|---|\n| 1 | 2 |"
    out = to_telegram_html(md)
    assert "##" not in out
    assert "**" not in out
    assert "|---|" not in out
    # Balanced bold tags.
    assert out.count("<b>") == out.count("</b>")


def test_empty() -> None:
    assert to_telegram_html("") == ""
