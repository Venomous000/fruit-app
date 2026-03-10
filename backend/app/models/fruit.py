from sqlalchemy import Boolean, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Fruit(Base):
    __tablename__ = "fruits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    color: Mapped[str] = mapped_column(String, nullable=False, index=True)
    in_season: Mapped[bool] = mapped_column(Boolean, nullable=False)