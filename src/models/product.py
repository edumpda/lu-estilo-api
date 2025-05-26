from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    sale_value = Column(Float, nullable=False)
    barcode = Column(String, unique=True, index=True, nullable=True) # Code de barras pode ser opcional
    section = Column(String, index=True, nullable=True) # Categoria/Seção
    initial_stock = Column(Integer, nullable=False, default=0)
    current_stock = Column(Integer, nullable=False, default=0) # Adicionando estoque atual
    validity_date = Column(Date, nullable=True)
    # Para imagens, uma abordagem simples é armazenar URLs ou caminhos
    # Uma abordagem mais robusta envolveria uma tabela separada para imagens
    image_urls = Column(Text, nullable=True) # Armazenar URLs separadas por vírgula ou JSON

    # Relationships (if needed later, e.g., order items)
    # order_items = relationship("OrderItem", back_populates="product")

# Poderia ter uma tabela separada para imagens se necessário
# class ProductImage(Base):
#     __tablename__ = "product_images"
#     id = Column(Integer, primary_key=True)
#     url = Column(String, nullable=False)
#     product_id = Column(Integer, ForeignKey("products.id"))
#     product = relationship("Product", back_populates="images")

# Product.images = relationship("ProductImage", back_populates="product")

