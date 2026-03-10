"""
HTTP integration tests for GET /fruit.

All tests hit the real FastAPI router via TestClient.
The database is an in-memory SQLite instance injected through
the `client` / `seeded_client` fixtures defined in conftest.py.

Fixture reference (from conftest.py)
-------------------------------------
  client         - TestClient + empty DB
  seeded_client  - TestClient + 11 pre-seeded fruits

Seed counts (for quick reference)
----------------------------------
  Total            : 11
  in_season=True   :  7  (Apple, Banana, Orange, Strawberry, Peach, Pineapple, Mango)
  in_season=False  :  4  (Grapes, Watermelon, Pear, Kiwi)
  color=red        :  3  (Apple-T, Watermelon-F, Strawberry-T)
  color=yellow     :  3  (Banana-T, Pineapple-T, Mango-T)
  color=orange     :  2  (Orange-T, Peach-T)
"""


# Response structure

class TestResponseStructure:
    def test_top_level_keys_present(self, seeded_client):
        """Response envelope must contain total, page, page_size, items."""
        resp = seeded_client.get("/fruit")
        assert resp.status_code == 200
        body = resp.json()
        for key in ("total", "page", "page_size", "items"):
            assert key in body, f"Missing top-level key: '{key}'"

    def test_item_fields_present(self, seeded_client):
        """Each item must have id, name, color, in_season."""
        body = seeded_client.get("/fruit").json()
        item = body["items"][0]
        for field in ("id", "name", "color", "in_season"):
            assert field in item, f"Missing item field: '{field}'"

    def test_item_types(self, seeded_client):
        """Field types must be correct: id=int, name/color=str, in_season=bool."""
        item = seeded_client.get("/fruit").json()["items"][0]
        assert isinstance(item["id"],        int)
        assert isinstance(item["name"],      str)
        assert isinstance(item["color"],     str)
        assert isinstance(item["in_season"], bool)

    def test_total_is_int(self, seeded_client):
        body = seeded_client.get("/fruit").json()
        assert isinstance(body["total"], int)


# Basic listing

class TestBasicListing:
    def test_returns_200(self, seeded_client):
        assert seeded_client.get("/fruit").status_code == 200

    def test_total_matches_seed_count(self, seeded_client):
        body = seeded_client.get("/fruit").json()
        assert body["total"] == 11

    def test_default_page_size_is_10(self, seeded_client):
        body = seeded_client.get("/fruit").json()
        assert len(body["items"]) == 10

    def test_default_page_is_1(self, seeded_client):
        body = seeded_client.get("/fruit").json()
        assert body["page"] == 1

    def test_empty_db_returns_empty_list(self, client):
        body = client.get("/fruit").json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_empty_db_status_200(self, client):
        assert client.get("/fruit").status_code == 200


# in_season filter

class TestInSeasonFilter:
    def test_in_season_true_total(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "true"}).json()
        assert body["total"] == 7

    def test_in_season_true_all_items_flagged(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "true"}).json()
        assert all(i["in_season"] is True for i in body["items"])

    def test_in_season_false_total(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "false"}).json()
        assert body["total"] == 4

    def test_in_season_false_all_items_flagged(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "false"}).json()
        assert all(i["in_season"] is False for i in body["items"])

    def test_in_season_true_contains_apple(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "true"}).json()
        names = [i["name"] for i in body["items"]]
        assert "Apple" in names

    def test_in_season_false_contains_grapes(self, seeded_client):
        body = seeded_client.get("/fruit", params={"in_season": "false"}).json()
        names = [i["name"] for i in body["items"]]
        assert "Grapes" in names

    def test_in_season_true_and_false_totals_sum_to_all(self, seeded_client):
        t = seeded_client.get("/fruit", params={"in_season": "true"}).json()["total"]
        f = seeded_client.get("/fruit", params={"in_season": "false"}).json()["total"]
        assert t + f == 11


# name filter

class TestNameFilter:
    def test_exact_name_match(self, seeded_client):
        # "apple" is a substring of both "Apple" AND "Pineapple" → 2 results
        body = seeded_client.get("/fruit", params={"name": "Apple"}).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert "Apple" in names
        assert "Pineapple" in names

    def test_lowercase_exact_match(self, seeded_client):
        body = seeded_client.get("/fruit", params={"name": "apple"}).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert "Apple" in names
        assert "Pineapple" in names

    def test_uppercase_exact_match(self, seeded_client):
        body = seeded_client.get("/fruit", params={"name": "APPLE"}).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert "Apple" in names
        assert "Pineapple" in names

    def test_partial_substring_match(self, seeded_client):
        # "app" is a substring of both "Apple" and "Pineapple"
        body = seeded_client.get("/fruit", params={"name": "app"}).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert "Apple" in names
        assert "Pineapple" in names

    def test_partial_matches_multiple_fruits(self, seeded_client):
        # "an" appears in Banana, Orange, Mango
        body = seeded_client.get("/fruit", params={"name": "an"}).json()
        names = {i["name"] for i in body["items"]}
        assert {"Banana", "Orange", "Mango"}.issubset(names)

    def test_fuzzy_typo_single_char_missing(self, seeded_client):
        # "aple" is missing one 'p' — fuzzy fallback should return Apple
        body = seeded_client.get("/fruit", params={"name": "aple"}).json()
        assert body["total"] >= 1
        names = [i["name"] for i in body["items"]]
        assert "Apple" in names

    def test_fuzzy_typo_transposition(self, seeded_client):
        # "bnaana" is a scrambled Banana — fuzzy should recover it
        body = seeded_client.get("/fruit", params={"name": "bnaana"}).json()
        names = [i["name"] for i in body["items"]]
        assert "Banana" in names

    def test_name_no_match_returns_empty(self, seeded_client):
        body = seeded_client.get("/fruit", params={"name": "zzzzzzzzz"}).json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_name_filter_empty_db(self, client):
        body = client.get("/fruit", params={"name": "Apple"}).json()
        assert body["total"] == 0


# color filter

class TestColorFilter:
    def test_exact_color_match(self, seeded_client):
        body = seeded_client.get("/fruit", params={"color": "red"}).json()
        assert body["total"] == 3
        assert all(i["color"] == "red" for i in body["items"])

    def test_color_case_insensitive(self, seeded_client):
        body = seeded_client.get("/fruit", params={"color": "RED"}).json()
        assert body["total"] == 3

    def test_color_uppercase(self, seeded_client):
        body = seeded_client.get("/fruit", params={"color": "YELLOW"}).json()
        assert body["total"] == 3

    def test_color_partial_substring(self, seeded_client):
        # "ello" is a substring of "yellow"
        body = seeded_client.get("/fruit", params={"color": "ello"}).json()
        assert body["total"] == 3

    def test_color_fuzzy_typo(self, seeded_client):
        # "yellw" → should still find yellow fruits
        body = seeded_client.get("/fruit", params={"color": "yellw"}).json()
        assert body["total"] >= 1
        assert all(i["color"] == "yellow" for i in body["items"])

    def test_color_no_match_returns_empty(self, seeded_client):
        body = seeded_client.get("/fruit", params={"color": "zzzzz"}).json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_color_orange_count(self, seeded_client):
        body = seeded_client.get("/fruit", params={"color": "orange"}).json()
        assert body["total"] == 2  # Orange, Peach


# Combined filters

class TestCombinedFilters:
    def test_name_and_in_season(self, seeded_client):
        # "apple" matches Apple(T) and Pineapple(T) — both are in season → 2
        body = seeded_client.get(
            "/fruit", params={"name": "Apple", "in_season": "true"}
        ).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert "Apple" in names
        assert "Pineapple" in names
        assert all(i["in_season"] is True for i in body["items"])

    def test_name_and_in_season_no_match(self, seeded_client):
        # Apple is in_season=True, so asking for False yields 0
        body = seeded_client.get(
            "/fruit", params={"name": "Apple", "in_season": "false"}
        ).json()
        assert body["total"] == 0

    def test_color_and_in_season_true(self, seeded_client):
        # Red fruits in season: Apple, Strawberry  (Watermelon is out)
        body = seeded_client.get(
            "/fruit", params={"color": "red", "in_season": "true"}
        ).json()
        assert body["total"] == 2
        names = {i["name"] for i in body["items"]}
        assert names == {"Apple", "Strawberry"}

    def test_color_and_in_season_false(self, seeded_client):
        # Red fruits out of season: only Watermelon
        body = seeded_client.get(
            "/fruit", params={"color": "red", "in_season": "false"}
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Watermelon"

    def test_all_three_filters(self, seeded_client):
        body = seeded_client.get(
            "/fruit",
            params={"name": "Mango", "color": "yellow", "in_season": "true"},
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Mango"

    def test_conflicting_filters_return_empty(self, seeded_client):
        # No fruit is named "Kiwi" AND colored "red"
        body = seeded_client.get(
            "/fruit", params={"name": "Kiwi", "color": "red"}
        ).json()
        assert body["total"] == 0


# Pagination

class TestPagination:
    def test_default_pagination_values(self, seeded_client):
        body = seeded_client.get("/fruit").json()
        assert body["page"] == 1
        assert body["page_size"] == 10

    def test_first_page_has_10_items(self, seeded_client):
        body = seeded_client.get("/fruit", params={"page": 1, "page_size": 10}).json()
        assert len(body["items"]) == 10

    def test_second_page_has_remaining_items(self, seeded_client):
        # 11 total, page_size=10 → page 2 has 1 item
        body = seeded_client.get("/fruit", params={"page": 2, "page_size": 10}).json()
        assert body["page"] == 2
        assert len(body["items"]) == 1

    def test_custom_page_size(self, seeded_client):
        body = seeded_client.get("/fruit", params={"page_size": 5}).json()
        assert body["page_size"] == 5
        assert len(body["items"]) == 5

    def test_page_beyond_results_is_empty(self, seeded_client):
        body = seeded_client.get("/fruit", params={"page": 999}).json()
        assert body["items"] == []

    def test_total_unaffected_by_pagination(self, seeded_client):
        # total always reflects the full filtered count, not the page slice
        body = seeded_client.get("/fruit", params={"page": 2, "page_size": 10}).json()
        assert body["total"] == 11

    def test_page_size_100_returns_all(self, seeded_client):
        body = seeded_client.get("/fruit", params={"page_size": 100}).json()
        assert len(body["items"]) == 11

    def test_page_size_1_returns_single_item(self, seeded_client):
        body = seeded_client.get("/fruit", params={"page_size": 1}).json()
        assert len(body["items"]) == 1

    def test_three_pages_cover_all_results(self, seeded_client):
        # 11 fruits with page_size=4 → pages [4, 4, 3]
        p1 = seeded_client.get("/fruit", params={"page": 1, "page_size": 4}).json()
        p2 = seeded_client.get("/fruit", params={"page": 2, "page_size": 4}).json()
        p3 = seeded_client.get("/fruit", params={"page": 3, "page_size": 4}).json()
        assert len(p1["items"]) == 4
        assert len(p2["items"]) == 4
        assert len(p3["items"]) == 3
        # ids across pages must be unique (no duplicates between pages)
        all_ids = (
            [i["id"] for i in p1["items"]]
            + [i["id"] for i in p2["items"]]
            + [i["id"] for i in p3["items"]]
        )
        assert len(all_ids) == len(set(all_ids))

    def test_pagination_with_name_filter(self, seeded_client):
        # "an" matches Banana, Orange, Mango (3) → page_size=2 → page 2 has 1
        p2 = seeded_client.get(
            "/fruit", params={"name": "an", "page": 2, "page_size": 2}
        ).json()
        assert p2["total"] == 3
        assert len(p2["items"]) == 1


# Input validation (FastAPI Query constraints → 422)

class TestInputValidation:
    def test_page_zero_is_rejected(self, seeded_client):
        assert seeded_client.get("/fruit", params={"page": 0}).status_code == 422

    def test_page_negative_is_rejected(self, seeded_client):
        assert seeded_client.get("/fruit", params={"page": -1}).status_code == 422

    def test_page_size_zero_is_rejected(self, seeded_client):
        assert seeded_client.get("/fruit", params={"page_size": 0}).status_code == 422

    def test_page_size_negative_is_rejected(self, seeded_client):
        assert seeded_client.get("/fruit", params={"page_size": -5}).status_code == 422

    def test_page_size_101_is_rejected(self, seeded_client):
        # le=100 constraint
        assert seeded_client.get("/fruit", params={"page_size": 101}).status_code == 422

    def test_page_size_100_is_accepted(self, seeded_client):
        # boundary value: exactly 100 is valid
        assert seeded_client.get("/fruit", params={"page_size": 100}).status_code == 200

    def test_page_size_1_is_accepted(self, seeded_client):
        assert seeded_client.get("/fruit", params={"page_size": 1}).status_code == 200

    def test_invalid_in_season_string_is_rejected(self, seeded_client):
        # FastAPI cannot coerce "maybe" to bool → 422
        assert (
            seeded_client.get("/fruit", params={"in_season": "maybe"}).status_code
            == 422
        )

    def test_invalid_page_string_is_rejected(self, seeded_client):
        assert (
            seeded_client.get("/fruit", params={"page": "abc"}).status_code == 422
        )
