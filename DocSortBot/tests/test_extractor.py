import pytest
from docsortbot.extractor import determine_year_from_text

def test_determine_year_anchor():
    text = "Here is some random text. Statement Period: Jan 1, 2023. More text."
    assert determine_year_from_text(text) == ("2023", "Anchor Keyword")

def test_determine_year_top_heavy():
    text = "Bank Document\nDate: 01/15/2023\n" + "x" * 2000 + "\nCopyright 2022\nCopyright 2022\nCopyright 2022"
    # Even though 2022 appears 3 times, 2023 is in the top 25%, so it should win
    assert determine_year_from_text(text) == ("2023", "Top-Heavy Frequency")

def test_determine_year_frequency():
    # 2022 appears most in the entire document, but not in the top 25%
    text = "some text " * 100 + "2022 " * 20 + "2023 " * 5
    assert determine_year_from_text(text) == ("2022", "Document-Wide Frequency")

def test_determine_year_tie():
    # Tie between 2020 and 2021, should pick 2021 (most recent)
    text = "some text " * 100 + "2020 " * 10 + "2021 " * 10
    assert determine_year_from_text(text) == ("2021", "Document-Wide Frequency")
