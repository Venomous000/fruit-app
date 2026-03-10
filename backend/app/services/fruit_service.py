from sqlalchemy import select
from app.models.fruit import Fruit
from rapidfuzz import process, fuzz

FUZZY_THRESHOLD = 70

class FruitService:

    def __init__(self, db):
        self.db = db

    def _fuzzy_filter(self, items, query_str, key_fn):
        """Case-insensitive partial match, falling back to fuzzy on no results."""
        q = query_str.lower()
        partial = [f for f in items if q in key_fn(f).lower()]
        if partial:
            return partial
        value_map = {key_fn(f).lower(): f for f in items}
        matches = process.extract(q, list(value_map.keys()), scorer=fuzz.WRatio, limit=None)
        return [value_map[m[0]] for m in matches if m[1] >= FUZZY_THRESHOLD]

    def get_fruits(self, color, in_season, name, page, page_size):
        query = select(Fruit)

        if in_season is not None:
            query = query.where(Fruit.in_season == in_season)

        all_results = self.db.execute(query).scalars().all()

        if name:
            all_results = self._fuzzy_filter(all_results, name, lambda f: f.name)

        if color:
            all_results = self._fuzzy_filter(all_results, color, lambda f: f.color)

        total = len(all_results)
        paginated = all_results[(page - 1) * page_size : page * page_size]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": f.id,
                    "name": f.name,
                    "color": f.color,
                    "in_season": f.in_season,
                }
                for f in paginated
            ],
        }
