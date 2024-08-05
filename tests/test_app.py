import unittest
import random

from peewee import SqliteDatabase

from app import app
from peewee_db import Product, Category

test_db = SqliteDatabase(":memory:")


# Use test DB
class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Make test client
        self.app = app.test_client()
        # Propagate exceptions to the test client
        self.app.testing = True

        # Use test DB
        test_db.bind([Category, Product])
        test_db.connect()
        test_db.create_tables([Category, Product])

        # Create duplicated product
        Category.get_or_create(name="Test")
        Product.get_or_create(name="Duplicate", price=100, category=1)

    def tearDown(self):
        # Delete duplicated product
        Product.delete().where(Product.name == "Duplicate").execute()
        # Delete test products
        Product.delete().where(Product.name.startswith("test_")).execute()

        Category.delete().where(Category.name == "Test").execute()

        # Close test DB
        test_db.drop_tables([Category, Product])
        test_db.close()

    def test_products_get(self):
        response = self.app.get("/products")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)

    def test_product_get_by_name_exist(self):
        response = self.app.get("/products?name=duplicate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0].get("name"), "Duplicate")

    def test_product_get_by_name_empty(self):
        response = self.app.get("/products?name=not_exist")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)


    def test_products_post(self):
        unique_product_name = f"test_{random.randint(1, 1000000)}"
        response = self.app.post("/products", json={"name": unique_product_name, "price": "100", "category": 1})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["name"], unique_product_name)
        self.assertEqual(float(response.json["price"]), 100)

    def test_product_post_duplicate_name(self):
        response = self.app.post("/products", json={"name": "Duplicate", "price": 100, "category": 1})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Product with this name already exists")

    def test_product_post_invalid_data(self):
        response = self.app.post("/products", json={"name": "Invalid", "price": "invalid"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Price must be a number")
