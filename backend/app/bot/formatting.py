"""Convert the model's Markdown into Telegram-safe HTML.

Telegram's HTML parse mode supports only a small tag set (``b i u s a code pre
blockquote tg-spoiler``) — **not** headings, lists or tables. LLMs love all
three, so we translate:

* ``**bold**`` / ``__bold__`` → ``<b>``; ``*italic*`` / ``_italic_`` → ``<i>``;
  ``~~strike~~`` → ``<s>``; `` `code` `` → ``<code>``; ```` ```blocks``` ```` → ``<pre>``;
  ``[text](url)`` → ``<a>``.
* ``#``/``##``/``###`` headings → a bold line.
* ``- `` / ``* `` bullets → ``• ``; numbered lists are kept.
* Markdown tables → a readable per-row block (first column bolded as a title,
  the rest as ``label: value`` bullets) since Telegram can't render tables.

The output is always valid Telegram HTML with balanced tags; everything is HTML-
escaped first so stray ``<``/``&`` in the model output can never break parsing.
"""

from __future__ import annotations

import html
import re

_FENCE_RE = re.compile(r"```[ \t]*([\w+-]*)\n?(.*?)```", re.DOTALL)
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
_BOLD_RE = re.compile(r"(\*\*|__)(.+?)\1", re.DOTALL)
_ITALIC_RE = re.compile(r"(?<![\w*])[*_]([^*_\n]+)[*_](?![\w*])")
_STRIKE_RE = re.compile(r"~~(.+?)~~", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
_BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_HR_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")


def _inline(text: str) -> str:
    """Apply inline Markdown → HTML on already-escaped text."""
    # Inline code first so its contents aren't touched by other rules.
    code_spans: list[str] = []

    def _stash_code(m: re.Match[str]) -> str:
        code_spans.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(code_spans) - 1}\x00"

    text = _INLINE_CODE_RE.sub(_stash_code, text)
    text = _LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD_RE.sub(r"<b>\2</b>", text)
    text = _STRIKE_RE.sub(r"<s>\1</s>", text)
    text = _ITALIC_RE.sub(r"<i>\1</i>", text)

    def _restore_code(m: re.Match[str]) -> str:
        return code_spans[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", _restore_code, text)


def _is_table_sep(line: str) -> bool:
    s = line.strip().strip("|")
    return bool(s) and set(s.replace(" ", "")) <= {"-", ":", "|"}


def _split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _render_table(header: list[str], rows: list[list[str]]) -> list[str]:
    """Telegram can't draw tables — render each row as a titled block."""
    out: list[str] = []
    for row in rows:
        if not any(row):
            continue
        title = _inline(row[0]) if row else ""
        # Avoid <b><b>…</b></b> when the cell was already bold in Markdown.
        if not (title.startswith("<b>") and title.endswith("</b>")):
            title = f"<b>{title}</b>"
        out.append(title)
        for i in range(1, len(row)):
            label = header[i] if i < len(header) else ""
            value = row[i]
            if not value:
                continue
            if label:
                out.append(f"• {_inline(label)}: {_inline(value)}")
            else:
                out.append(f"• {_inline(value)}")
        out.append("")  # blank line between rows
    if out and out[-1] == "":
        out.pop()
    return out


def to_telegram_html(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 1. Pull out fenced code blocks; restore them last so nothing reformats them.
    blocks: list[str] = []

    def _stash_block(m: re.Match[str]) -> str:
        code = html.escape(m.group(2).rstrip("\n"))
        blocks.append(f"<pre>{code}</pre>")
        return f"\x01{len(blocks) - 1}\x01"

    text = _FENCE_RE.sub(_stash_block, text)

    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i]

        # Restore a code block placeholder occupying its own line.
        stash = re.fullmatch(r"\x01(\d+)\x01", raw.strip())
        if stash:
            out.append(blocks[int(stash.group(1))])
            i += 1
            continue

        # Markdown table: a header row with pipes followed by a separator row.
        if "|" in raw and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            header = _split_row(raw)
            j = i + 2
            rows: list[list[str]] = []
            while j < len(lines) and "|" in lines[j] and not _is_table_sep(lines[j]):
                rows.append(_split_row(lines[j]))
                j += 1
            out.extend(_render_table(header, rows))
            i = j
            continue

        if _HR_RE.match(raw):
            i += 1
            continue

        escaped = html.escape(raw)

        heading = _HEADING_RE.match(raw)
        if heading:
            out.append(f"<b>{_inline(html.escape(heading.group(1)))}</b>")
            i += 1
            continue

        bullet = _BULLET_RE.match(raw)
        if bullet:
            indent = "  " * (len(bullet.group(1)) // 2)
            out.append(f"{indent}• {_inline(html.escape(bullet.group(2)))}")
            i += 1
            continue

        out.append(_inline(escaped))
        i += 1

    result = "\n".join(out)
    # Collapse 3+ blank lines that block conversion may introduce.
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result
