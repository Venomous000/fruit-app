import json
import os
from pathlib import Path

from app.core.database import SessionLocal, Base, engine
from app.models.fruit import Fruit

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "fruitList.json"

def seed():
    session = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        if not DATA_PATH.exists():
            print("No fruitList.json found at", DATA_PATH)
            return

        with open(DATA_PATH, "r", encoding="utf-8") as fh:
            items = json.load(fh)

        # optional: clear current table
        session.query(Fruit).delete()
        session.commit()

        objs = []
        for i, it in enumerate(items, start=1):
            objs.append(
                Fruit(
                    name=it.get("name"),
                    color=it.get("color", [""])[0],
                    in_season=bool(it.get("in_season")),
                )
            )
        session.bulk_save_objects(objs)
        session.commit()
        print(f"Seeded {len(objs)} fruits.")
    finally:
        session.close()

if __name__ == "__main__":
    seed()