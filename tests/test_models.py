# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
# ######################################################################
    # #  MY  T E S T   C A S E S 
    # ######################################################################

    def test_read_a_product(self):
        """It should Read a Product"""
        # Create a Product object using the ProductFactory
        product = ProductFactory()
        # Add a log message displaying the product for debugging errors
        # Use logger.info for standard messages, change level if needed for debugging
        app.logger.info("Creating product: %s", product)
        # Set the ID of the product object to None and then create the product.
        product.id = None
        product.create()
        # Assert that the product ID is not None
        self.assertIsNotNone(product.id)
        # Fetch the product back from the database
        found_product = Product.find(product.id)
        # Assert the properties of the found product are correct
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(Decimal(found_product.price), product.price) # Compare as Decimal
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        # Create a Product object using the ProductFactory
        product = ProductFactory()
        # Add a log message displaying the product for debugging errors
        app.logger.info("Creating product for update: %s", product)
        # Set the ID of the product object to None and create the product.
        product.id = None
        product.create()
        # Log the product object again after it has been created
        app.logger.info("Product created: %s", product)
        self.assertIsNotNone(product.id)
        original_id = product.id # Store original ID

        # Update the description property of the product object.
        new_description = "UPDATED DESCRIPTION"
        product.description = new_description
        product.update()

        # Assert that that the id and description properties of the product object have been updated correctly.
        self.assertEqual(product.id, original_id) # ID should not change
        self.assertEqual(product.description, new_description) # Description on instance should be new

        # Fetch all products from the database to verify that after updating the product,
        # there is only one product in the system.
        # (Fetch the specific product by ID is more direct)
        fetched_product = Product.find(original_id)
        self.assertIsNotNone(fetched_product)

        # Assert that the fetched product has the original id but updated description.
        self.assertEqual(fetched_product.id, original_id)
        self.assertEqual(fetched_product.description, new_description)

        # Also check the count if required by interpretation
        all_products = Product.all()
        self.assertEqual(len(all_products), 1)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        # Create a Product object using the ProductFactory and save it to the database.
        product = ProductFactory()
        product.create()
        # Assert that after creating a product and saving it to the database,
        # there is only one product in the system.
        self.assertEqual(len(Product.all()), 1)
        # Remove the product from the database.
        product.delete()
        # Assert if the product has been successfully deleted from the database.
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        # Retrieve all products from the database and assign them to the products variable.
        products = Product.all()
        # Assert there are no products in the database at the beginning of the test case.
        self.assertEqual(products, [])
        # Create five products and save them to the database.
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # Fetching all products from the database again and assert the count is 5
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        # Create a batch of 5 Product objects using the ProductFactory and save them to the database.
        products_batch = ProductFactory.create_batch(5)
        for product in products_batch:
            product.create()
        # Retrieve the name of the first product in the products list
        name_to_find = products_batch[0].name
        # Count the number of occurrences of the product name in the list
        count = 0
        for product in products_batch:
            if product.name == name_to_find:
                count += 1
        app.logger.info("Expecting %d products with name '%s'", count, name_to_find)
        # Retrieve products from the database that have the specified name.
        found_products = Product.find_by_name(name_to_find)
        # Assert if the count of the found products matches the expected count.
        self.assertEqual(found_products.count(), count)
        # Assert that each product’s name matches the expected name.
        for product in found_products:
            self.assertEqual(product.name, name_to_find)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        # Create a batch of 10 Product objects using the ProductFactory and save them to the database.
        products_batch = ProductFactory.create_batch(10)
        for product in products_batch:
            product.create()
        # Retrieve the availability of the first product in the products list
        availability_to_find = products_batch[0].available
        # Count the number of occurrences of the product availability in the list
        count = 0
        for product in products_batch:
            if product.available == availability_to_find:
                count += 1
        app.logger.info("Expecting %d products with availability %s", count, availability_to_find)
        # Retrieve products from the database that have the specified availability.
        found_products = Product.find_by_availability(availability_to_find)
        # Assert if the count of the found products matches the expected count.
        self.assertEqual(found_products.count(), count)
        # Assert that each product's availability matches the expected availability.
        for product in found_products:
            self.assertEqual(product.available, availability_to_find)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        # Create a batch of 10 Product objects using the ProductFactory and save them to the database.
        products_batch = ProductFactory.create_batch(10)
        for product in products_batch:
            product.create()
        # Retrieve the category of the first product in the products list
        category_to_find = products_batch[0].category
        # Count the number of occurrences of the product that have the same category in the list.
        count = 0
        for product in products_batch:
            if product.category == category_to_find:
                count += 1
        app.logger.info("Expecting %d products with category %s", count, category_to_find.name)
        # Retrieve products from the database that have the specified category.
        found_products = Product.find_by_category(category_to_find)
        # Assert if the count of the found products matches the expected count.
        self.assertEqual(found_products.count(), count)
        # Assert that each product's category matches the expected category.
        for product in found_products:
            self.assertEqual(product.category, category_to_find)


    ######################################################################
    #  A D D I T I O N A L   H E L P E R   T E S T S (Example: Price, Ser/Deser)
    ######################################################################

    def test_find_by_price(self):
        """It should Find a Product by Price"""
        products_batch = ProductFactory.create_batch(5)
        for product in products_batch:
            product.create()
        price_to_find = products_batch[0].price
        count = 0
        for product in products_batch:
            if product.price == price_to_find:
                count += 1
        app.logger.info("Expecting %d products with price %s", count, price_to_find)
        found = Product.find_by_price(price_to_find)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(Decimal(product.price), price_to_find) # Compare as Decimal

        found_str = Product.find_by_price(str(price_to_find))
        self.assertEqual(found_str.count(), count)
        for product in found_str:
             self.assertEqual(Decimal(product.price), price_to_find)


    def test_serialize_a_product(self):
        """It should serialize a Product"""
        product = ProductFactory()
        data = product.serialize()
        self.assertIsNotNone(data)
        self.assertIn("id", data)
        self.assertEqual(data["id"], product.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], product.name)
        # ... (rest of assertions) ...
        self.assertIn("price", data)
        self.assertEqual(Decimal(data["price"]), product.price) # Compare as Decimal
        self.assertIn("available", data)
        self.assertEqual(data["available"], product.available)
        self.assertIn("category", data)
        self.assertEqual(data["category"], product.category.name) # Check against enum name

    def test_deserialize_a_product(self):
        """It should de-serialize a Product"""
        product_data = ProductFactory().serialize() # Get realistic data structure
        product = Product()
        product.deserialize(product_data)
        self.assertEqual(product.name, product_data["name"])
        self.assertEqual(product.description, product_data["description"])
        self.assertEqual(product.price, Decimal(product_data["price"]))
        self.assertEqual(product.available, product_data["available"])
        self.assertEqual(product.category.name, product_data["category"])
        # Note: ID is usually not set during deserialize from external data

    def test_deserialize_missing_data(self):
         """It should not deserialize a Product with missing data"""
         data = {"id": 1, "name": "test", "description": "test description"}
         product = Product()
         with self.assertRaises(DataValidationError) as cm:
             product.deserialize(data)
         self.assertTrue("missing" in str(cm.exception).lower()) # More general check for missing key error

    def test_deserialize_bad_data_type(self):
         """It should not deserialize a Product with bad data type"""
         data = ProductFactory().serialize()
         data["available"] = "not-a-boolean" # Invalid type
         product = Product()
         with self.assertRaises(DataValidationError) as cm:
             product.deserialize(data)
         self.assertIn("Invalid type for boolean [available]", str(cm.exception))

    def test_deserialize_bad_enum_value(self):
        """It should not deserialize a Product with bad enum value"""
        data = ProductFactory().serialize()
        data["category"] = "INVALID_CATEGORY" # Not a valid enum member name
        product = Product()
        with self.assertRaises(DataValidationError) as cm:
            product.deserialize(data)
        self.assertIn("Invalid attribute: INVALID_CATEGORY", str(cm.exception)) # Error comes from getattr

    def test_update_with_no_id(self):
        """It should raise DataValidationError when updating with no ID"""
        product = ProductFactory()
        product.id = None # Ensure ID is None
        with self.assertRaises(DataValidationError) as cm:
            product.update()
        self.assertIn("Update called with empty ID field", str(cm.exception))