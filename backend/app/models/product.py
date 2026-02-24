from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductCatalog(Base):
    __tablename__ = "product_catalog"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    ingredients_csv: Mapped[str] = mapped_column(String(1024))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    wc_id: Mapped[int] = mapped_column(Integer, nullable=True)
