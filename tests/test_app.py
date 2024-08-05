import random
import unittest

from peewee import SqliteDatabase

from app import app
from peewee_db import Product, Category

test_db = SqliteDatabase(":memory:")

CATEGORY_ENDPOINT = "/categories"
PRODUCT_ENDPOINT = "/products"
MOCK_CATEGORY_NAME = "Mock Category"
MOCK_PRODUCT_NAME = "Mock Product"


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
        Category.get_or_create(name=MOCK_CATEGORY_NAME)
        Product.get_or_create(name=MOCK_PRODUCT_NAME, price=100, category=1)

    def tearDown(self):
        Product.delete().where(Product.name.startswith(MOCK_PRODUCT_NAME)).execute()
        Category.delete().where(Category.name.startswith(MOCK_CATEGORY_NAME)).execute()

        # Close test DB
        test_db.drop_tables([Category, Product])
        test_db.close()

    def test_category_get(self):
        response = self.app.get(CATEGORY_ENDPOINT)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0].get("name"), MOCK_CATEGORY_NAME)

    def test_category_post(self):
        unique_name = f"{MOCK_PRODUCT_NAME}_{random.randint(1, 1000000)}"
        response = self.app.post(CATEGORY_ENDPOINT, json={"name": unique_name})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["name"], unique_name)

    def test_products_get(self):
        response = self.app.get(PRODUCT_ENDPOINT)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)

    def test_product_get_by_name_exist(self):
        response = self.app.get(f"{PRODUCT_ENDPOINT}?name={MOCK_PRODUCT_NAME.upper()}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0].get("name"), MOCK_PRODUCT_NAME)

    def test_product_get_by_name_empty(self):
        response = self.app.get(f"{PRODUCT_ENDPOINT}?name=not_exist")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

    def test_products_post(self):
        unique_product_name = f"{MOCK_PRODUCT_NAME}_{random.randint(1, 1000000)}"
        response = self.app.post(PRODUCT_ENDPOINT, json={"name": unique_product_name, "price": "100", "category": 1})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["name"], unique_product_name)
        self.assertEqual(float(response.json["price"]), 100)

    def test_product_post_duplicate_name(self):
        response = self.app.post("/products", json={"name": f"{MOCK_PRODUCT_NAME}", "price": 100, "category": 1})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Product with this name already exists")

    def test_product_post_invalid_data(self):
        response = self.app.post(PRODUCT_ENDPOINT, json={"name": "Invalid", "price": "invalid"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Price must be a number")

    def test_product_delete(self):
        delete_response = self.app.delete(f"{PRODUCT_ENDPOINT}/1")
        product_response = self.app.get(f"{PRODUCT_ENDPOINT}?name={MOCK_PRODUCT_NAME}")

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(len(product_response.json), 0)

    def test_product_delete_error(self):
        response = self.app.delete(f"{PRODUCT_ENDPOINT}/0")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Product not found")
