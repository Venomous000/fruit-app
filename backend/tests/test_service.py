"""
Unit tests for FruitService and its private _fuzzy_filter helper.

Two layers of testing:
  1. _fuzzy_filter  – pure logic, no database.
                      Uses a simple _Stub object instead of a real Fruit model.
  2. get_fruits     – uses a real SQLite session from the seeded_session fixture.
                      Tests the full data-fetch + filter + paginate flow.

Fixtures (from conftest.py)
----------------------------
  db_session      – clean empty SQLite session
  seeded_session  – SQLite session pre-loaded with 11 fruits

Seed counts
-----------
  Total            : 11
  in_season=True   :  7  (Apple, Banana, Orange, Strawberry, Peach, Pineapple, Mango)
  in_season=False  :  4  (Grapes, Watermelon, Pear, Kiwi)
  color=red        :  3  (Apple-T, Watermelon-F, Strawberry-T)
  color=yellow     :  3  (Banana-T, Pineapple-T, Mango-T)
  color=orange     :  2  (Orange-T, Peach-T)
"""

import pytest
from app.services.fruit_service import FruitService, FUZZY_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# Minimal stub used by _fuzzy_filter tests — no DB, no SQLAlchemy needed
# ─────────────────────────────────────────────────────────────────────────────

class _Stub:
    """Lightweight stand-in for a Fruit ORM object."""
    def __init__(self, name: str, color: str):
        self.name  = name
        self.color = color

    def __repr__(self):
        return f"<Stub name={self.name!r} color={self.color!r}>"


@pytest.fixture
def svc():
    """FruitService with db=None — only _fuzzy_filter is exercised."""
    return FruitService(db=None)


# ─────────────────────────────────────────────────────────────────────────────
# _fuzzy_filter — substring (fast-path) behaviour
# ─────────────────────────────────────────────────────────────────────────────

class TestFuzzyFilterSubstring:
    def test_exact_full_name_matches(self, svc):
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow")]
        result = svc._fuzzy_filter(items, "Apple", lambda f: f.name)
        assert len(result) == 1
        assert result[0].name == "Apple"

    def test_partial_substring_matches(self, svc):
        items = [_Stub("Apple", "red"), _Stub("Pineapple", "yellow"), _Stub("Banana", "yellow")]
        result = svc._fuzzy_filter(items, "app", lambda f: f.name)
        names = {f.name for f in result}
        # "app" is a substring of both "Apple" and "Pineapple"
        assert names == {"Apple", "Pineapple"}

    def test_case_insensitive_uppercase_query(self, svc):
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow")]
        result = svc._fuzzy_filter(items, "APPLE", lambda f: f.name)
        assert len(result) == 1
        assert result[0].name == "Apple"

    def test_case_insensitive_mixed_case_query(self, svc):
        items = [_Stub("Apple", "red")]
        result = svc._fuzzy_filter(items, "aPpLe", lambda f: f.name)
        assert len(result) == 1

    def test_substring_returns_multiple_when_appropriate(self, svc):
        items = [_Stub("Pear", "green"), _Stub("Peach", "orange"), _Stub("Banana", "yellow")]
        result = svc._fuzzy_filter(items, "pe", lambda f: f.name)
        names = {f.name for f in result}
        assert "Pear"  in names
        assert "Peach" in names
        assert "Banana" not in names

    def test_key_fn_used_for_color_field(self, svc):
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow"), _Stub("Strawberry", "red")]
        result = svc._fuzzy_filter(items, "red", lambda f: f.color)
        names = {f.name for f in result}
        assert names == {"Apple", "Strawberry"}

    def test_empty_items_list_returns_empty(self, svc):
        result = svc._fuzzy_filter([], "apple", lambda f: f.name)
        assert result == []

    def test_substring_match_skips_fuzzy_entirely(self, svc):
        # "ban" is a substring → substring path should return before rapidfuzz
        items = [_Stub("Banana", "yellow"), _Stub("Apple", "red")]
        result = svc._fuzzy_filter(items, "ban", lambda f: f.name)
        assert len(result) == 1
        assert result[0].name == "Banana"


# ─────────────────────────────────────────────────────────────────────────────
# _fuzzy_filter — rapidfuzz fallback behaviour
# ─────────────────────────────────────────────────────────────────────────────

class TestFuzzyFilterFuzzyFallback:
    def test_typo_single_char_missing(self, svc):
        # "aple" has no substring match in any name → fuzzy kicks in
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow"), _Stub("Grapes", "purple")]
        result = svc._fuzzy_filter(items, "aple", lambda f: f.name)
        assert len(result) >= 1
        assert result[0].name == "Apple"

    def test_typo_extra_char(self, svc):
        # "appple" → should still score high enough for Apple
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow")]
        result = svc._fuzzy_filter(items, "appple", lambda f: f.name)
        names = [f.name for f in result]
        assert "Apple" in names

    def test_no_match_below_threshold_returns_empty(self, svc):
        # "xzq" has no substring match and an extremely low fuzzy score
        items = [_Stub("Banana", "yellow"), _Stub("Grapes", "purple")]
        result = svc._fuzzy_filter(items, "xzq", lambda f: f.name)
        assert result == []

    def test_threshold_constant_is_correct_value(self):
        assert FUZZY_THRESHOLD == 70

    def test_fuzzy_fallback_color_typo(self, svc):
        # "yellw" → no substring match, fuzzy should find "yellow"
        items = [_Stub("Banana", "yellow"), _Stub("Apple", "red")]
        result = svc._fuzzy_filter(items, "yellw", lambda f: f.color)
        assert len(result) >= 1
        assert all(f.color == "yellow" for f in result)

    def test_gibberish_returns_empty_list(self, svc):
        items = [_Stub("Apple", "red"), _Stub("Banana", "yellow"), _Stub("Kiwi", "brown")]
        result = svc._fuzzy_filter(items, "qqqqqqqq", lambda f: f.name)
        assert result == []

    def test_single_item_list_typo_match(self, svc):
        items = [_Stub("Watermelon", "red")]
        result = svc._fuzzy_filter(items, "watermeln", lambda f: f.name)
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — no filters (full table)
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsNoFilter:
    def test_total_is_11(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 100)
        assert result["total"] == 11

    def test_returns_all_items_when_page_size_large(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 100)
        assert len(result["items"]) == 11

    def test_response_contains_required_keys(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 10)
        for key in ("total", "page", "page_size", "items"):
            assert key in result

    def test_item_contains_required_fields(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 1)
        item = result["items"][0]
        for field in ("id", "name", "color", "in_season"):
            assert field in item

    def test_empty_db_returns_zero_total(self, db_session):
        result = FruitService(db_session).get_fruits(None, None, None, 1, 10)
        assert result["total"] == 0
        assert result["items"] == []

    def test_page_and_page_size_echoed_in_response(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 3, 7)
        assert result["page"] == 3
        assert result["page_size"] == 7


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — in_season filter
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsInSeasonFilter:
    def test_in_season_true_count(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, True, None, 1, 100)
        assert result["total"] == 7

    def test_in_season_true_all_items_flagged(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, True, None, 1, 100)
        assert all(i["in_season"] is True for i in result["items"])

    def test_in_season_false_count(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, False, None, 1, 100)
        assert result["total"] == 4

    def test_in_season_false_all_items_flagged(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, False, None, 1, 100)
        assert all(i["in_season"] is False for i in result["items"])

    def test_in_season_none_returns_all(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 100)
        assert result["total"] == 11

    def test_true_and_false_counts_sum_to_total(self, seeded_session):
        t = FruitService(seeded_session).get_fruits(None, True,  None, 1, 100)["total"]
        f = FruitService(seeded_session).get_fruits(None, False, None, 1, 100)["total"]
        assert t + f == 11


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — name filter
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsNameFilter:
    def test_exact_name(self, seeded_session):
        # "apple" is a substring of both "Apple" and "Pineapple" → 2 results
        result = FruitService(seeded_session).get_fruits(None, None, "Apple", 1, 100)
        assert result["total"] == 2
        names = {i["name"] for i in result["items"]}
        assert "Apple" in names
        assert "Pineapple" in names

    def test_partial_name(self, seeded_session):
        # "app" is a substring of both "Apple" and "Pineapple"
        result = FruitService(seeded_session).get_fruits(None, None, "app", 1, 100)
        assert result["total"] == 2

    def test_name_case_insensitive(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, "MANGO", 1, 100)
        assert result["total"] == 1
        assert result["items"][0]["name"] == "Mango"

    def test_name_fuzzy_typo(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, "aple", 1, 100)
        names = [i["name"] for i in result["items"]]
        assert "Apple" in names

    def test_name_no_match(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, "zzzzzzz", 1, 100)
        assert result["total"] == 0
        assert result["items"] == []

    def test_name_partial_matches_multiple(self, seeded_session):
        # "an" is substring of Banana, Orange, Mango
        result = FruitService(seeded_session).get_fruits(None, None, "an", 1, 100)
        names = {i["name"] for i in result["items"]}
        assert {"Banana", "Orange", "Mango"}.issubset(names)


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — color filter
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsColorFilter:
    def test_color_red_count(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("red", None, None, 1, 100)
        assert result["total"] == 3

    def test_color_red_all_items_correct(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("red", None, None, 1, 100)
        assert all(i["color"] == "red" for i in result["items"])

    def test_color_yellow_count(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("yellow", None, None, 1, 100)
        assert result["total"] == 3

    def test_color_case_insensitive(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("RED", None, None, 1, 100)
        assert result["total"] == 3

    def test_color_no_match(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("zzzzz", None, None, 1, 100)
        assert result["total"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — combined filters
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsCombinedFilters:
    def test_red_and_in_season_true(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("red", True, None, 1, 100)
        assert result["total"] == 2
        names = {i["name"] for i in result["items"]}
        assert names == {"Apple", "Strawberry"}

    def test_red_and_in_season_false(self, seeded_session):
        result = FruitService(seeded_session).get_fruits("red", False, None, 1, 100)
        assert result["total"] == 1
        assert result["items"][0]["name"] == "Watermelon"

    def test_name_and_in_season(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, True, "banana", 1, 100)
        assert result["total"] == 1
        assert result["items"][0]["name"] == "Banana"

    def test_conflicting_filters_return_empty(self, seeded_session):
        # Kiwi is brown, not red — intersection is empty
        result = FruitService(seeded_session).get_fruits("red", None, "Kiwi", 1, 100)
        assert result["total"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# get_fruits — pagination
# ─────────────────────────────────────────────────────────────────────────────

class TestGetFruitsPagination:
    def test_page_1_page_size_5(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 1, 5)
        assert len(result["items"]) == 5
        assert result["total"] == 11

    def test_page_2_page_size_5(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 2, 5)
        assert len(result["items"]) == 5

    def test_page_3_page_size_5_has_one_item(self, seeded_session):
        # 11 fruits / page_size=5 → page 3 has 1 item
        result = FruitService(seeded_session).get_fruits(None, None, None, 3, 5)
        assert len(result["items"]) == 1

    def test_beyond_last_page_is_empty(self, seeded_session):
        result = FruitService(seeded_session).get_fruits(None, None, None, 99, 10)
        assert result["items"] == []
        assert result["total"] == 11  # total still correct

    def test_total_reflects_filtered_not_paginated_count(self, seeded_session):
        # yellow fruits = 3, page_size=2 → items has 2, total has 3
        result = FruitService(seeded_session).get_fruits("yellow", None, None, 1, 2)
        assert result["total"] == 3
        assert len(result["items"]) == 2

    def test_no_duplicate_ids_across_pages(self, seeded_session):
        p1 = FruitService(seeded_session).get_fruits(None, None, None, 1, 4)
        p2 = FruitService(seeded_session).get_fruits(None, None, None, 2, 4)
        p3 = FruitService(seeded_session).get_fruits(None, None, None, 3, 4)
        ids = (
            [i["id"] for i in p1["items"]]
            + [i["id"] for i in p2["items"]]
            + [i["id"] for i in p3["items"]]
        )
        assert len(ids) == len(set(ids))

    def test_page_size_1_iterates_correctly(self, seeded_session):
        # 11 pages of 1 item each — all ids should be unique
        ids = []
        for page in range(1, 12):
            r = FruitService(seeded_session).get_fruits(None, None, None, page, 1)
            assert len(r["items"]) == 1
            ids.append(r["items"][0]["id"])
        assert len(set(ids)) == 11
