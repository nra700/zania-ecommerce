# from fastapi import FastAPI, HTTPException, status, Depends
# from pydantic import BaseModel
# from typing import List
# from sqlalchemy import Column, Integer, String, Float
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship
# from sqlalchemy import create_engine

# # Create a SQLAlchemy engine and session
# DATABASE_URL = "sqlite:///./test.db"  # Example SQLite database, change to your own
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Create SQLAlchemy base model
# Base = declarative_base()

# # Product model in SQLAlchemy
# class Product(Base):
#     __tablename__ = "products"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     price = Column(Float)
#     stock = Column(Integer)

# # Order model in SQLAlchemy
# class Order(Base):
#     __tablename__ = "orders"
#     id = Column(Integer, primary_key=True, index=True)
#     total_price = Column(Float)
#     status = Column(String)

# # OrderProduct model in SQLAlchemy (to link products to orders)
# class OrderProduct(Base):
#     __tablename__ = "order_products"
#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(Integer, index=True)
#     product_id = Column(Integer, index=True)
#     quantity = Column(Integer)

# # Pydantic model for Product
# class ProductResponse(BaseModel):
#     product_id: int
#     quantity: int

# # Pydantic model for OrderResponse (used for the response)
# class OrderResponse(BaseModel):
#     id: int
#     total_price: float
#     status: str
#     products: List[ProductResponse]

#     class Config:
#         orm_mode = True  # This ensures the Pydantic model works with SQLAlchemy ORM objects

# # FastAPI app
# app = FastAPI()

# # Dependency to get the database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Create the database tables if they don't exist
# Base.metadata.create_all(bind=engine)

# @app.post("/orders/", response_model=OrderResponse)
# def create_order(products_in_order: List[ProductResponse], db: SessionLocal = Depends(get_db)):
#     if not products_in_order:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No products provided in the order.")

#     total_price = 0
#     products = []

#     try:
#         for item in products_in_order:
#             product = db.query(Product).filter(Product.id == item.product_id).first()
#             if not product:
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found.")

#             if product.stock < item.quantity:
#                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}.")

#             product.stock -= item.quantity
#             db.commit()  # Save the updated stock

#             total_price += product.price * item.quantity
#             products.append({"product_id": product.id, "quantity": item.quantity})

#         # Create the order
#         new_order = Order(total_price=total_price, status="pending")
#         db.add(new_order)
#         db.commit()
#         db.refresh(new_order)

#         # Save the products in the OrderProduct model
#         for item in products_in_order:
#             db.add(OrderProduct(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))
#         db.commit()

#         # Return the response with order details
#         return OrderResponse(
#             id=new_order.id,
#             total_price=new_order.total_price,
#             status=new_order.status,
#             products=products
#         )

#     except Exception as e:
#         db.rollback()  # Rollback any transaction in case of failure
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# # Get all products
# @app.get("/products/", response_model=List[ProductResponse])
# def get_products(db: SessionLocal = Depends(get_db)):
#     products = db.query(Product).all()
#     return [{"product_id": product.id, "quantity": 0} for product in products]  # Returning products with quantity 0 (to be filled by user)

# ----------------
# from fastapi import FastAPI, HTTPException, Depends
# from pydantic import BaseModel, Field
# from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
# from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
# from typing import List

# # Database setup
# DATABASE_URL = "sqlite:///./test.db"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Models
# class Product(Base):
#     __tablename__ = "products"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     description = Column(String, nullable=False)
#     price = Column(Float, nullable=False)
#     stock = Column(Integer, nullable=False)

# class Order(Base):
#     __tablename__ = "orders"
#     id = Column(Integer, primary_key=True, index=True)
#     total_price = Column(Float, nullable=False)
#     status = Column(String, default="pending", nullable=False)
#     order_products = relationship("OrderProduct", back_populates="order")

# class OrderProduct(Base):
#     __tablename__ = "order_products"
#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
#     product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     order = relationship("Order", back_populates="order_products")

# # Create tables
# Base.metadata.create_all(bind=engine)

# # Pydantic schemas
# class ProductCreate(BaseModel):
#     name: str
#     description: str
#     price: float
#     stock: int

# class ProductResponse(ProductCreate):
#     id: int

#     class Config:
#         orm_mode = True

# class OrderProductCreate(BaseModel):
#     product_id: int
#     quantity: int

# class OrderCreate(BaseModel):
#     products: List[OrderProductCreate]

# class OrderResponse(BaseModel):
#     id: int
#     total_price: float
#     status: str
#     products: List[OrderProductCreate] = Field(...)

#     class Config:
#         orm_mode = True

# # Dependency for database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # FastAPI application
# app = FastAPI()

# # Routes
# @app.get("/products", response_model=List[ProductResponse])
# def get_products(db: Session = Depends(get_db)):
#     products = db.query(Product).all()
#     return products

# @app.post("/products", response_model=ProductResponse)
# def create_product(product: ProductCreate, db: Session = Depends(get_db)):
#     db_product = Product(**product.dict())
#     db.add(db_product)
#     db.commit()
#     db.refresh(db_product)
#     return db_product

# @app.post("/orders", response_model=OrderResponse)
# def create_order(order: OrderCreate, db: Session = Depends(get_db)):
#     total_price = 0
#     order_products = []
    
#     for item in order.products:
#         product = db.query(Product).filter(Product.id == item.product_id).first()
#         if not product:
#             raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
#         if product.stock < item.quantity:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Insufficient stock for product ID {item.product_id}"
#             )
#         product.stock -= item.quantity
#         total_price += product.price * item.quantity
#         order_products.append(OrderProduct(product_id=product.id, quantity=item.quantity))
    
#     new_order = Order(total_price=total_price, status="pending")
#     db.add(new_order)
#     db.commit()
#     db.refresh(new_order)
    
#     for op in order_products:
#         op.order_id = new_order.id
#         db.add(op)
#     db.commit()
    
#     return {
#         "id": new_order.id,
#         "total_price": new_order.total_price,
#         "status": new_order.status,
#         "products": [{"product_id": op.product_id, "quantity": op.quantity} for op in order_products],
#     }

# @app.get("/orders/{order_id}", response_model=OrderResponse)
# def get_order(order_id: int, db: Session = Depends(get_db)):
#     order = db.query(Order).filter(Order.id == order_id).first()
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return {
#         "id": order.id,
#         "total_price": order.total_price,
#         "status": order.status,
#         "products": [
#             {"product_id": op.product_id, "quantity": op.quantity}
#             for op in order.order_products
#         ],
#     }

from fastapi import FastAPI, HTTPException, Depends
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
