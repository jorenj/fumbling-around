import pytest
from docsortbot.extractor import determine_year_from_text

def test_determine_year_ignores_money():
    text = "Here is some text with $2000 and 2000.00 and 2000.50. The actual year is 2025."
    assert determine_year_from_text(text) == ("2025", "Top-Heavy Frequency")

def test_determine_year_anchor_w2():
    text = "Form W-2 Wage and Tax Statement 2026. Some other text with 2000 and 2000."
    assert determine_year_from_text(text) == ("2026", "Anchor Keyword")
