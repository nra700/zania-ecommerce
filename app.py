from fastapi import FastAPI, HTTPException, Depends
from mangum import Mangum
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from typing import List

# Database setup
DATABASE_URL = "sqlite:///./test2.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending", nullable=False)
    order_products = relationship("OrderProduct", back_populates="order")

class OrderProduct(Base):
    __tablename__ = "order_products"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="order_products")
    product = relationship("Product")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int

class ProductResponse(ProductCreate):
    id: int

    class Config:
        from_attributes = True

class OrderProductCreate(BaseModel):
    product_id: int
    quantity: int

class ProductDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int

class OrderProductResponse(BaseModel):
    product_id: int
    quantity: int
    name: str
    description: str
    price: float
    stock: int

class OrderCreate(BaseModel):
    products: List[OrderProductCreate]

class OrderResponse(BaseModel):
    id: int
    total_price: float
    status: str
    products: List[OrderProductResponse]

    class Config:
        from_attributes = True

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI application
app = FastAPI()

# Routes
@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    total_price = 0
    order_products = []
    
    for item in order.products:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product ID {item.product_id}"
            )
        product.stock -= item.quantity
        total_price += product.price * item.quantity
        order_products.append(OrderProduct(product_id=product.id, quantity=item.quantity))
    
    new_order = Order(total_price=total_price, status="pending")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    for op in order_products:
        op.order_id = new_order.id
        db.add(op)
    db.commit()
    
    return {
        "id": new_order.id,
        "total_price": new_order.total_price,
        "status": new_order.status,
        "products": [
            {
                "product_id": op.product_id,
                "quantity": op.quantity,
                "name": op.product.name,
                "description": op.product.description,
                "price": op.product.price,
                "stock": op.product.stock
            }
            for op in order_products
        ],
    }

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_products_details = []
    for op in order.order_products:
        product = op.product
        order_products_details.append({
            "product_id": product.id,
            "quantity": op.quantity,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock
        })
    
    return {
        "id": order.id,
        "total_price": order.total_price,
        "status": order.status,
        "products": order_products_details,
    }

handler = Mangum(app)
