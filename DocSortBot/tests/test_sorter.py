import pytest
from pathlib import Path
from docsortbot.sorter import extract_year

def test_extract_year_single():
    dummy = Path("dummy.pdf")
    assert extract_year("Statement_2023.pdf", dummy) == ("2023", False, "Filename Match")
    assert extract_year("2024-01-Statement.csv", dummy) == ("2024", False, "Filename Match")
    assert extract_year("Receipt_1999_12_31.png", dummy) == ("1999", False, "Filename Match")

def test_extract_year_none():
    dummy = Path("dummy.pdf")
    assert extract_year("Statement.pdf", dummy) == (None, False, None)
    assert extract_year("Statement_1234.pdf", dummy) == (None, False, None)
    assert extract_year("Statement_2100.pdf", dummy) == (None, False, None)

def test_extract_year_duplicate_same_year():
    dummy = Path("dummy.pdf")
    # If the same year appears twice, it's still a single unique year
    assert extract_year("Statement_2023_2023.pdf", dummy) == ("2023", False, "Filename Match")

def test_extract_year_conflicting_years():
    dummy = Path("dummy.pdf")
    # If there are conflicting years, we should return None
    assert extract_year("Statement_2023_2024.pdf", dummy) == (None, False, None)
    assert extract_year("2021_Receipt_2022.jpg", dummy) == (None, False, None)
