import unittest
from unittest import mock

class TestIntegration(unittest.TestCase):
    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)
        self.order = None

    def setUp(self):
        # 初始化 UserRegistration, RestaurantBrowsing, Cart 和 PaymentProcessing 实例
        self.registration = UserRegistration()
        self.database = mock.Mock()  # 模拟数据库
        self.browsing = RestaurantBrowsing(self.database)
        self.cart = Cart()
        #self.order = OrderPlacement(self.cart)
        self.payment_processing = PaymentProcessing()
        self.database.get_restaurants.return_value = [
            {"name": "Italian Bistro", "cuisine": "Italian", "location": "Downtown", "rating": 4.5}
        ]
        # 创建一个模拟的用户配置文件
        self.user_profile = UserProfile(delivery_address="123 Main St")

        # 创建一个模拟的餐厅菜单
        self.restaurant_menu = RestaurantMenu(available_items=["Pizza", "Burger", "Salad"])

        # 创建 OrderPlacement 的实例，并传入购物车和用户配置文件
        self.order = OrderPlacement(self.cart, self.user_profile, self.restaurant_menu)

    def test_user_registration_integration(self):
        # 注册用户
        self.registration.register("user@example.com", "Password123", "Password123")

        # 模拟 get_user 方法的返回值
        self.database.get_user.return_value = {
            'email': "user@example.com",
            'password': "Password123"  # 如果需要，可以添加其他字段
        }

        # 验证用户数据存储
        user_data = self.database.get_user("user@example.com")
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data['email'], "user@example.com")

    def test_restaurant_browsing_integration(self):
        # 插入测试餐厅数据
        self.database.insert_restaurant({"name": "Italian Bistro", "cuisine": "Italian", "rating": 4.5})

        # 调用 search_by_filters 方法
        results = self.browsing.search_by_filters(cuisine_type="Italian", location="Downtown", min_rating=4.0)

        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Italian Bistro")

    def test_cart_order_integration(self):
        # 添加商品到购物车
        self.cart.add_item("Pizza", 12.99, 1)
        # 创建订单
        order = self.order.create_order()


    def test_payment_processing_integration(self):
        order = {"total_amount": 100.00}
        payment_details = {"card_number": "1234567812345678", "expiry_date": "12/25", "cvv": "123"}
        with mock.patch.object(self.payment_processing, 'mock_payment_gateway', return_value={"status": "success"}):
            result = self.payment_processing.process_payment(order, "credit_card", payment_details)
            self.assertEqual(result, "Payment successful, Order confirmed")


class UserRegistration:
    def __init__(self):
        """
        Initializes the UserRegistration class with an empty dictionary to store user data.
        Each entry in the dictionary will map an email to a dictionary containing the user's password and confirmation status.
        """
        self.users = {}

    def register(self, email, password, confirm_password):
        """
        Registers a new user.

        This function takes an email, password, and password confirmation as input. It performs a series of checks to ensure the registration
        is valid:
        - Verifies that the email is in a valid format.
        - Ensures that the password matches the confirmation password.
        - Validates that the password meets the strength requirements.
        - Checks if the email is already registered.

        If all checks pass, the user is registered, and their email and password are stored in the `users` dictionary, along with a confirmation
        status set to False (indicating the user is not yet confirmed). A success message is returned.

        Args:
            email (str): The user's email address.
            password (str): The user's password.
            confirm_password (str): Confirmation of the user's password.

        Returns:
            dict: A dictionary containing the result of the registration attempt.
                  On success, it returns {"success": True, "message": "Registration successful, confirmation email sent"}.
                  On failure, it returns {"success": False, "error": "Specific error message"}.
        """
        if not self.is_valid_email(email):
            return {"success": False, "error": "Invalid email format"}  # If email format is invalid, return an error.
        if password != confirm_password:
            return {"success": False, "error": "Passwords do not match"}  # If passwords don't match, return an error.
        if not self.is_strong_password(password):
            return {"success": False,
                    "error": "Password is not strong enough"}  # If password isn't strong, return an error.
        if email in self.users:
            return {"success": False,
                    "error": "Email already registered"}  # If the email is already registered, return an error.

        # Register the user if all conditions are met and return a success message.
        self.users[email] = {"password": password, "confirmed": False}
        return {"success": True, "message": "Registration successful, confirmation email sent"}

    def is_valid_email(self, email):
        """
        Checks if the provided email is valid based on a simple validation rule.
        This rule only checks that the email contains an '@' symbol and has a '.' in the domain part.

        Args:
            email (str): The email address to be validated.

        Returns:
            bool: True if the email is valid, False otherwise.
        """
        return "@" in email and "." in email.split("@")[-1]

    def is_strong_password(self, password):
        """
        Checks if the provided password meets the strength requirements.
        A strong password is defined as one that is at least 8 characters long, contains at least one letter, and at least one number.

        Args:
            password (str): The password to be validated.

        Returns:
            bool: True if the password is strong, False otherwise.
        """
        return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)


class RestaurantBrowsing:
    """
    A class for browsing restaurants in a database based on various criteria like cuisine type, location, and rating.

    Attributes:
        database (RestaurantDatabase): An instance of RestaurantDatabase that holds restaurant data.
    """

    def __init__(self, database):
        """
        Initialize RestaurantBrowsing with a reference to a restaurant database.

        Args:
            database (RestaurantDatabase): The database object containing restaurant information.
        """
        self.database = database

    def search_by_cuisine(self, cuisine_type):
        """
        Search for restaurants based on their cuisine type.

        Args:
            cuisine_type (str): The type of cuisine to filter by (e.g., "Italian").

        Returns:
            list: A list of restaurants that match the given cuisine type.
        """
        return [restaurant for restaurant in self.database.get_restaurants()
                if restaurant['cuisine'].lower() == cuisine_type.lower()]

    def search_by_location(self, location):
        """
        Search for restaurants based on their location.

        Args:
            location (str): The location to filter by (e.g., "Downtown").

        Returns:
            list: A list of restaurants that are located in the specified area.
        """
        return [restaurant for restaurant in self.database.get_restaurants()
                if restaurant['location'].lower() == location.lower()]

    def search_by_rating(self, min_rating):
        """
        Search for restaurants based on their minimum rating.

        Args:
            min_rating (float): The minimum acceptable rating to filter by (e.g., 4.0).

        Returns:
            list: A list of restaurants that have a rating greater than or equal to the specified rating.
        """
        return [restaurant for restaurant in self.database.get_restaurants()
                if restaurant['rating'] >= min_rating]

    def search_by_filters(self, cuisine_type=None, location=None, min_rating=None):
        """
        Search for restaurants based on multiple filters: cuisine type, location, and/or rating.

        Args:
            cuisine_type (str, optional): The type of cuisine to filter by.
            location (str, optional): The location to filter by.
            min_rating (float, optional): The minimum acceptable rating to filter by.

        Returns:
            list: A list of restaurants that match all specified filters.
        """
        results = self.database.get_restaurants()  # Start with all restaurants

        if cuisine_type:
            results = [restaurant for restaurant in results
                       if restaurant['cuisine'].lower() == cuisine_type.lower()]

        if location:
            results = [restaurant for restaurant in results
                       if restaurant['location'].lower() == location.lower()]

        if min_rating:
            results = [restaurant for restaurant in results
                       if restaurant['rating'] >= min_rating]

        return results


class Cart:
    """
    Represents a shopping cart that can contain multiple CartItem objects.

    Attributes:
        items (list): A list of CartItem objects in the cart.
    """

    def __init__(self):
        """
        Initializes an empty Cart with no items.
        """
        self.items = []

    def calculate_total(self):
        # 计算所有商品的总金额
        return sum(item.get_subtotal() for item in self.items)

    def add_item(self, name, price, quantity):
        """
        Adds a new item to the cart or updates the quantity of an existing item.

        Args:
            name (str): Name of the item.
            price (float): Price of the item.
            quantity (int): Quantity to be added to the cart.

        Returns:
            str: A message indicating whether the item was added or updated.
        """
        for item in self.items:
            if item.name == name:
                # If the item is already in the cart, update its quantity.
                item.update_quantity(item.quantity + quantity)
                return f"Updated {name} quantity to {item.quantity}"

        # If the item is not in the cart, add it as a new item.
        new_item = CartItem(name, price, quantity)
        self.items.append(new_item)
        return f"Added {name} to cart"

    def remove_item(self, name):
        """
        Removes an item from the cart by its name.

        Args:
            name (str): Name of the item to be removed.

        Returns:
            str: A message indicating the item was removed.
        """
        self.items = [item for item in self.items if item.name != name]
        return f"Removed {name} from cart"

    def update_item_quantity(self, name, new_quantity):
        """
        Updates the quantity of an item in the cart by its name.

        Args:
            name (str): Name of the item.
            new_quantity (int): The new quantity for the item.

        Returns:
            str: A message indicating whether the item's quantity was updated or if the item was not found.
        """
        for item in self.items:
            if item.name == name:
                item.update_quantity(new_quantity)
                return f"Updated {name} quantity to {new_quantity}"
        return f"{name} not found in cart"

    def calculate_total(self):
        """
        Calculates the total cost of the items in the cart, including tax and delivery fee.

        Returns:
            dict: A dictionary containing the subtotal, tax, delivery fee, and total cost.
        """
        subtotal = sum(item.get_subtotal() for item in self.items)
        tax = subtotal * 0.10  # Assume 10% tax rate.
        delivery_fee = 5.00  # Flat delivery fee.
        total = subtotal + tax + delivery_fee
        return {"subtotal": subtotal, "tax": tax, "delivery_fee": delivery_fee, "total": total}

    def view_cart(self):
        """
        Provides a view of the items in the cart.

        Returns:
            list: A list of dictionaries with each item's name, quantity, and subtotal price.
        """
        return [{"name": item.name, "quantity": item.quantity, "subtotal": item.get_subtotal()} for item in self.items]


class OrderPlacement:
    """
    Represents the process of placing an order, including validation, checkout, and confirmation.

    Attributes:
        cart (Cart): The shopping cart containing the items for the order.
        user_profile (UserProfile): The user's profile, including delivery address.
        restaurant_menu (RestaurantMenu): The menu containing available restaurant items.
    """

    def __init__(self, cart, user_profile, restaurant_menu):
        """
        Initializes an OrderPlacement object with the cart, user profile, and restaurant menu.

        Args:
            cart (Cart): The shopping cart.
            user_profile (UserProfile): The user's profile.
            restaurant_menu (RestaurantMenu): The restaurant menu with available items.
        """
        self.cart = cart
        self.user_profile = user_profile
        self.restaurant_menu = restaurant_menu

    def create_order(self):
        # 计算购物车中的总金额
        total_amount = self.cart.calculate_total()  # 确保这个方法存在并返回总金额

        # 创建并返回一个订单对象
        if total_amount > 0:
            return Order(total_amount)  # 返回一个包含 total_amount 的订单对象
        else:
            return None  # 如果总金额为 0，返回 None

    def validate_order(self):
        """
        Validates the order by checking if the cart is empty and if all items are available in the restaurant menu.

        Returns:
            dict: A dictionary indicating whether the order is valid and an accompanying message.
        """
        if not self.cart.items:
            return {"success": False, "message": "Cart is empty"}

        # Validate the availability of each item in the cart.
        for item in self.cart.items:
            if not self.restaurant_menu.is_item_available(item.name):
                return {"success": False, "message": f"{item.name} is not available"}
        return {"success": True, "message": "Order is valid"}

    def proceed_to_checkout(self):
        """
        Prepares the order for checkout by calculating the total and retrieving the delivery address.

        Returns:
            dict: A dictionary containing the cart items, total cost details, and delivery address.
        """
        total_info = self.cart.calculate_total()
        return {
            "items": self.cart.view_cart(),
            "total_info": total_info,
            "delivery_address": self.user_profile.delivery_address,
        }

    def confirm_order(self, payment_method):
        """
        Confirms the order by validating it and processing the payment.

        Args:
            payment_method (PaymentMethod): The method of payment to be used.

        Returns:
            dict: A dictionary indicating whether the order was confirmed and an order ID if successful.
        """
        if not self.validate_order()["success"]:
            return {"success": False, "message": "Order validation failed"}

        # Process payment using the given payment method.
        payment_success = payment_method.process_payment(self.cart.calculate_total()["total"])

        if payment_success:
            return {
                "success": True,
                "message": "Order confirmed",
                "order_id": "ORD123456",  # Simulate an order ID.
                "estimated_delivery": "45 minutes"
            }
        return {"success": False, "message": "Payment failed"}

    def create_order(self):
        pass

class Order:
    def __init__(self, total_amount):
        self.total_amount = total_amount

class PaymentProcessing:
    """
    The PaymentProcessing class handles validation and processing of payments using different payment methods.

    Attributes:
        available_gateways (list): A list of supported payment gateways such as 'credit_card' and 'paypal'.
    """

    def __init__(self):
        """
        Initializes the PaymentProcessing class with available payment gateways.
        """
        self.available_gateways = ["credit_card", "paypal"]

    def validate_payment_method(self, payment_method, payment_details):
        """
        Validates the selected payment method and its associated details.

        Args:
            payment_method (str): The selected payment method (e.g., 'credit_card', 'paypal').
            payment_details (dict): The details required for the payment method (e.g., card number, expiry date).

        Returns:
            bool: True if the payment method and details are valid, otherwise raises ValueError.

        Raises:
            ValueError: If the payment method is not supported or if the payment details are invalid.
        """
        # Check if the payment method is supported.
        if payment_method not in self.available_gateways:
            raise ValueError("Invalid payment method")

        # Validate credit card details if the selected method is 'credit_card'.
        if payment_method == "credit_card":
            if not self.validate_credit_card(payment_details):
                raise ValueError("Invalid credit card details")

        # Validation passed.
        return True

    def validate_credit_card(self, details):
        """
        Validates the credit card details (e.g., card number, expiry date, CVV).

        Args:
            details (dict): A dictionary containing 'card_number', 'expiry_date', and 'cvv'.

        Returns:
            bool: True if the card details are valid, False otherwise.
        """
        card_number = details.get("card_number", "")
        expiry_date = details.get("expiry_date", "")
        cvv = details.get("cvv", "")

        # Basic validation: Check if the card number is 16 digits and CVV is 3 digits.
        if len(card_number) != 16 or len(cvv) != 3:
            return False

        # More advanced validations like the Luhn Algorithm for card number can be added here.
        return True

    def process_payment(self, order, payment_method, payment_details):
        """
        Processes the payment for an order, validating the payment method and interacting with the payment gateway.

        Args:
            order (dict): The order details, including total amount.
            payment_method (str): The selected payment method.
            payment_details (dict): The details required for the payment method.

        Returns:
            str: A message indicating whether the payment was successful or failed.
        """
        try:
            # Validate the payment method and details.
            self.validate_payment_method(payment_method, payment_details)

            # Simulate interaction with the payment gateway.
            payment_response = self.mock_payment_gateway(payment_method, payment_details, order["total_amount"])

            # Return the appropriate message based on the payment gateway's response.
            if payment_response["status"] == "success":
                return "Payment successful, Order confirmed"
            else:
                return "Payment failed, please try again"

        except Exception as e:
            # Catch and return any validation or processing errors.
            return f"Error: {str(e)}"

    def mock_payment_gateway(self, method, details, amount):
        """
        Simulates the interaction with a payment gateway for processing payments.

        Args:
            method (str): The payment method (e.g., 'credit_card').
            details (dict): The payment details (e.g., card number).
            amount (float): The amount to be charged.

        Returns:
            dict: A mock response from the payment gateway, indicating success or failure.
        """
        # Simulate card decline for a specific card number.
        if method == "credit_card" and details["card_number"] == "1111222233334444":
            return {"status": "failure", "message": "Card declined"}

        # Mock a successful transaction.
        return {"status": "success", "transaction_id": "abc123"}


class CartItem:
    """
    Represents an individual item in the shopping cart.

    Attributes:
        name (str): The name of the item.
        price (float): The price of the item.
        quantity (int): The quantity of the item in the cart.
    """

    def __init__(self, name, price, quantity):
        """
        Initializes a CartItem object with the given name, price, and quantity.

        Args:
            name (str): Name of the item.
            price (float): Price of the item.
            quantity (int): Quantity of the item in the cart.
        """
        self.name = name
        self.price = price
        self.quantity = quantity

    def update_quantity(self, new_quantity):
        """
        Updates the quantity of the item in the cart.

        Args:
            new_quantity (int): The new quantity of the item.
        """
        self.quantity = new_quantity

    def get_subtotal(self):
        """
        Calculates the subtotal price for this item based on its price and quantity.

        Returns:
            float: The subtotal price for this item.
        """
        return self.price * self.quantity


class UserProfile:
    """
    Represents the user's profile, including delivery address.

    Attributes:
        delivery_address (str): The user's delivery address.
    """

    def __init__(self, delivery_address):
        """
        Initializes a UserProfile object with a delivery address.

        Args:
            delivery_address (str): The user's delivery address.
        """
        self.delivery_address = delivery_address


class RestaurantMenu:
    """
    Represents the restaurant's menu, including available items.

    Attributes:
        available_items (list): A list of items available on the restaurant's menu.
    """

    def __init__(self, available_items):
        """
        Initializes a RestaurantMenu with a list of available items.

        Args:
            available_items (list): A list of available menu items.
        """
        self.available_items = available_items

    def is_item_available(self, item_name):
        """
        Checks if a specific item is available in the restaurant's menu.

        Args:
            item_name (str): The name of the item to check.

        Returns:
            bool: True if the item is available, False otherwise.
        """
        return item_name in self.available_items


if __name__ == "__main__":
    unittest.main()
