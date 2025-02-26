from pathlib import Path
import re
import sys
from py2md.main import (
    is_comment,
    remove_comment_syntax,
    extract_blocks,
    build_markdown,
    Block,
    unescape_mathjax,
)


def test_is_comment():
    """Test that lines starting with triple quotes are recognized as comment markers."""
    assert is_comment('"""This is a comment') is True
    assert is_comment("'''Another comment") is True
    # Lines that do not start with the comment syntax should return False.
    assert is_comment("Not a comment") is False
    # Leading spaces are not trimmed by our implementation.
    assert is_comment('  """Indented comment') is False


def test_remove_comment_syntax():
    """Test that the triple-quote syntax is removed properly."""
    # Removal from the beginning of a line.
    assert remove_comment_syntax('"""Hello world') == "Hello world"
    assert remove_comment_syntax("'''Hello world") == "Hello world"
    # Removal from the end of a line.
    assert remove_comment_syntax('Goodbye world"""') == "Goodbye world"
    assert remove_comment_syntax("Goodbye world'''") == "Goodbye world"
    # When quotes are in the middle, nothing should be changed.
    assert remove_comment_syntax('Hello """ world') == 'Hello """ world'
    # When both starting and ending quotes are present, all are removed.
    line = "'''Hello world'''"
    assert remove_comment_syntax(line) == "Hello world"


def test_extract_blocks(tmp_path):
    """Test extracting blocks from a temporary Python file containing both code and comment blocks."""
    file_content = (
        '"""Header comment\n'
        "Still header comment\n"
        '"""\n'
        'print("Hello World")\n'
        '"""Footer comment\n'
        "More footer comment\n"
        '"""'
    )
    test_file = tmp_path / "test.py"
    test_file.write_text(file_content)

    blocks = extract_blocks(Path(test_file))
    # We expect three blocks: a header comment, a code block, and a footer comment.
    assert len(blocks) == 3

    # Verify the header comment block.
    assert not blocks[0].is_code
    expected_header = "Header comment\nStill header comment\n"
    assert blocks[0].content == expected_header

    # Verify the code block.
    assert blocks[1].is_code
    assert blocks[1].content.strip() == 'print("Hello World")'

    # Verify the footer comment block.
    assert not blocks[2].is_code
    expected_footer = "Footer comment\nMore footer comment\n"
    assert blocks[2].content == expected_footer


def test_build_markdown(tmp_path):
    """Test building a Markdown file from a list of blocks."""
    blocks = [
        Block("Header comment\n", is_code=False),
        Block("print('Hello')\n", is_code=True),
        Block("Footer comment\n", is_code=False),
    ]
    output_file = tmp_path / "output.md"
    build_markdown(blocks, Path(output_file))

    # Read the generated Markdown file.
    content = output_file.read_text()
    # Header and footer comments should appear as is.
    assert "Header comment" in content
    assert "Footer comment" in content
    # Code blocks should be wrapped with Markdown code fences.
    assert "```python" in content
    assert "print('Hello')" in content
    assert content.count("```") >= 2
    # There should be no occurrences of three or more consecutive newlines.
    assert not re.search(r"\n{3,}", content)


def test_unescape_mathjax_no_change():
    """Test that a string with no double backslashes remains unchanged."""
    text = "This is a normal text without mathjax."
    assert unescape_mathjax(text) == text


def test_unescape_mathjax_single_instance():
    """Test that a single occurrence of double backslashes is unescaped to a single backslash."""
    # The literal "$\\\\text{variable}$" produces a string with two backslashes.
    input_str = "$\\\\text{variable}$"
    # The expected output should have one backslash: "$\\text{variable}$"
    expected = "$\\text{variable}$"
    assert unescape_mathjax(input_str) == expected


def test_unescape_mathjax_multiple_instances():
    """Test that multiple occurrences of double backslashes are correctly unescaped."""
    # Each "$\\\\alpha" produces a string with two backslashes in each occurrence.
    input_str = "$\\\\alpha + \\\\beta = \\\\gamma$"
    # Expected output should replace each pair with a single backslash.
    expected = "$\\alpha + \\beta = \\gamma$"
    assert unescape_mathjax(input_str) == expected


def test_unescape_mathjax_empty_string():
    """Test that an empty string remains unchanged."""
    assert unescape_mathjax("") == ""
