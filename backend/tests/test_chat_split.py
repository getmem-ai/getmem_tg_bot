from app.bot.handlers.chat import _split_message


def test_short_message_not_split() -> None:
    assert _split_message("hello") == ["hello"]


def test_long_message_split_into_chunks() -> None:
    text = "\n".join(f"line {i}" for i in range(2000))
    chunks = _split_message(text)
    assert len(chunks) > 1
    assert all(len(c) <= 4096 for c in chunks)
    assert "line 1999" in chunks[-1]


def test_split_without_newlines_hard_cuts() -> None:
    text = "x" * 9000
    chunks = _split_message(text)
    assert all(len(c) <= 4096 for c in chunks)
    assert "".join(chunks) == text
