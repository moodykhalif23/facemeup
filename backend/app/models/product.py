from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductCatalog(Base):
    __tablename__ = "product_catalog"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    ingredients_csv: Mapped[str] = mapped_column(String(1024))
    stock: Mapped[int] = mapped_column(Integer, default=0)
