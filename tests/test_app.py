import unittest
from fastapi.testclient import TestClient
from app import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Base, Product

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Setup the database for testing
Base.metadata.create_all(bind=engine)

# Test class
class TestFastAPIApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up resources for all tests."""
        # Insert a sample product
        db = TestingSessionLocal()
        sample_product = Product(name="Test Product", description="Sample", price=10.99, stock=10)
        db.add(sample_product)
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests."""
        Base.metadata.drop_all(bind=engine)

    def test_create_product(self):
        response = client.post("/products", json={
            "name": "New Product",
            "description": "A new product",
            "price": 15.99,
            "stock": 20
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "New Product")
        self.assertEqual(data["price"], 15.99)
        self.assertEqual(data["stock"], 20)

    def test_get_products(self):
        response = client.get("/products")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)

    def test_create_order(self):
        response = client.post("/orders", json={
            "products": [
                {"product_id": 1, "quantity": 2}
            ]
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_price"], 0)
        self.assertEqual(data["status"], "pending")

    def test_get_order(self):
        response = client.get("/orders/1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], 1)
        self.assertGreater(len(data["products"]), 0)

# Entry point for running the tests
if __name__ == "__main__":
    unittest.main()
