######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
import urllib.parse # Added for URL encoding in query tests
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
# Make sure DataValidationError is imported if testing specific deserialize errors
from service.models import db, init_db, Product, DataValidationError, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()

        app.logger.error(new_product, test_product)
        print("XXXXXXXXXXXXXXXXXXX", new_product, test_product)
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

 #----------------------------------------------------------
    # TEST READ
    #----------------------------------------------------------
    def test_get_product(self):
        """It should Get a single Product"""
        # Create a product to read using the utility function
        test_product = self._create_products(1)[0]
        # Make a GET request to the API endpoint
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        # Assert that the return code was HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the json that was returned
        data = response.get_json()
        # Assert that it is equal to the data from the created product
        self.assertEqual(data["name"], test_product.name)
        self.assertEqual(data["description"], test_product.description)
        self.assertEqual(Decimal(data["price"]), test_product.price)
        self.assertEqual(data["available"], test_product.available)
        self.assertEqual(data["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        # Make a GET request call passing in an invalid product id 0
        response = self.client.get(f"{BASE_URL}/0")
        # Assert that the return code was HTTP_404_NOT_FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        app.logger.debug("Response data (Not Found): %s", data)
        # Assert that the message contains "was not found"
        self.assertIn("was not found", data["message"])

    #----------------------------------------------------------
    # TEST UPDATE
    #----------------------------------------------------------
    def test_update_product(self):
        """It should Update an existing Product"""
        # Create a product to update
        test_product = self._create_products(1)[0]
        # Get the serialized version and modify it
        update_data = test_product.serialize()
        update_data["description"] = "UPDATED DESCRIPTION"
        update_data["price"] = str(Decimal(update_data["price"]) + 10.00) # Update price too
        # Make a PUT request to the API endpoint
        response = self.client.put(f"{BASE_URL}/{test_product.id}", json=update_data)
        # Assert that the return code was HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the json that was returned
        updated_product_json = response.get_json()
        # Assert that the properties were updated correctly
        self.assertEqual(updated_product_json["id"], test_product.id) # ID should stay the same
        self.assertEqual(updated_product_json["description"], "UPDATED DESCRIPTION")
        self.assertEqual(Decimal(updated_product_json["price"]), Decimal(update_data["price"]))

        # Optional: Fetch it back via GET and confirm the update persisted
        fetch_resp = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(fetch_resp.status_code, status.HTTP_200_OK)
        fetched_product_json = fetch_resp.get_json()
        self.assertEqual(fetched_product_json["description"], "UPDATED DESCRIPTION")
        self.assertEqual(Decimal(fetched_product_json["price"]), Decimal(update_data["price"]))

    def test_update_product_not_found(self):
        """It should not Update a Product that is not found"""
        # Create some valid update data
        update_data = ProductFactory().serialize()
        update_data["description"] = "This should not be updated"
        # Make a PUT request to an invalid ID
        response = self.client.put(f"{BASE_URL}/0", json=update_data)
        # Assert that the return code was HTTP_404_NOT_FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    #----------------------------------------------------------
    # TEST DELETE
    #----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a Product"""
        # Create multiple products to ensure deletion works correctly
        products_list = self._create_products(5)
        initial_count = self.get_product_count() # Use provided helper
        self.assertEqual(initial_count, 5)

        # Select one product to delete from the list created by the helper
        product_to_delete = products_list[0]
        # Make a DELETE request to the API endpoint
        response = self.client.delete(f"{BASE_URL}/{product_to_delete.id}")
        # Assert that the return code was HTTP_204_NO_CONTENT
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Assert that the response data is empty
        self.assertEqual(response.data, b'')

        # Verify the product is gone
        # Check the count decreased by one using the helper
        self.assertEqual(self.get_product_count(), initial_count - 1)
        # Try to fetch the deleted product via GET
        fetch_resp = self.client.get(f"{BASE_URL}/{product_to_delete.id}")
        self.assertEqual(fetch_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_product(self):
        """It should return 204 NO CONTENT even if deleting a non-existing Product"""
        # Make a DELETE request for an ID that doesn't exist (e.g., 0)
        response = self.client.delete(f"{BASE_URL}/0")
        # Assert that the return code was HTTP_204_NO_CONTENT (DELETE is idempotent)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Assert that the response data is empty
        self.assertEqual(response.data, b'')

    #----------------------------------------------------------
    # TEST LIST / QUERY
    #----------------------------------------------------------
    def test_list_all_products(self):
        """It should List all Products in the database"""
        # Check if the list is empty initially (before creating any products)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), []) # Expect an empty list

        # Create multiple products using the helper
        num_products = 5
        self._create_products(num_products)

        # Make a GET request to the base URL to list products
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the list of products from the response JSON
        data = response.get_json()
        # Assert the count is correct
        self.assertEqual(len(data), num_products)

    def test_list_by_name(self):
        """It should List Products by name"""
        # Create multiple products using the helper
        products_list = self._create_products(10)
        # Get the name of the first product created
        target_name = products_list[0].name
        # Count how many of the created products actually have this name
        expected_count = 0
        for product in products_list:
            if product.name == target_name:
                expected_count += 1
        app.logger.info("Expecting %d products with name '%s'", expected_count, target_name)

        # Make a GET request with the name query parameter
        # URL encode the name to handle potential special characters
        encoded_name = urllib.parse.quote_plus(target_name)
        response = self.client.get(f"{BASE_URL}?name={encoded_name}")

        # Assert the status code is 200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the list of products from the response JSON
        data = response.get_json()
        # Assert the count matches the expected count
        self.assertEqual(len(data), expected_count)
        # Assert all returned products have the correct name
        for product_data in data:
            self.assertEqual(product_data["name"], target_name)

    def test_list_by_category(self):
        """It should List Products by category"""
        # Create multiple products using the helper
        products_list = self._create_products(10)
        # Get the category of the first product created
        target_category = products_list[0].category
        # Get the name of the category enum member (e.g., "CLOTHS")
        target_category_name = target_category.name
        # Count how many of the created products actually have this category
        expected_count = 0
        for product in products_list:
            if product.category == target_category:
                expected_count += 1
        app.logger.info("Expecting %d products with category '%s'", expected_count, target_category_name)

        # Make a GET request with the category query parameter
        response = self.client.get(f"{BASE_URL}?category={target_category_name}")

        # Assert the status code is 200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the list of products from the response JSON
        data = response.get_json()
        # Assert the count matches the expected count
        self.assertEqual(len(data), expected_count)
        # Assert all returned products have the correct category name
        for product_data in data:
            self.assertEqual(product_data["category"], target_category_name)

    def test_list_by_availability(self):
        """It should List Products by availability"""
        # Create multiple products using the helper
        products_list = self._create_products(10)
        # Get the availability status of the first product created
        target_availability = products_list[0].available
        # Convert the boolean to its lowercase string representation for the URL ('true' or 'false')
        availability_str = str(target_availability).lower()
        # Count how many of the created products actually have this availability status
        expected_count = 0
        for product in products_list:
            if product.available == target_availability:
                expected_count += 1
        app.logger.info("Expecting %d products with availability '%s'", expected_count, availability_str)

        # Make a GET request with the availability query parameter
        response = self.client.get(f"{BASE_URL}?available={availability_str}")

        # Assert the status code is 200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get the list of products from the response JSON
        data = response.get_json()
        # Assert the count matches the expected count
        self.assertEqual(len(data), expected_count)
        # Assert all returned products have the correct availability status
        for product_data in data:
            self.assertEqual(product_data["available"], target_availability)


    ######################################################################
    # Utility functions (Keep get_product_count as it's used)
    ######################################################################

    def get_product_count(self):
        """save the current number of products by querying the list endpoint"""
        response = self.client.get(BASE_URL)
        # This assertion assumes the LIST endpoint works correctly
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

