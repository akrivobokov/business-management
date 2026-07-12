from django.test import TestCase, Client
from orders.models import Product, Order, OrderProduct
import json

class OrderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product1 = Product.objects.create(
            name="Product 1",
            description="A test product",
            price=10.50,
            stock=100
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            description="Another test product",
            price=20.00,
            stock=50
        )

    def test_create_order_success(self):
        response = self.client.post('/orders/create/', {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'product_ids': [self.product1.id, self.product2.id],
            'quantities': [2, 1]
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Order created')
        self.assertIn('order_id', data)

        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.customer_email, 'john@example.com')
        self.assertEqual(order.total_price, 41.00)

        order_products = OrderProduct.objects.filter(order=order)
        self.assertEqual(order_products.count(), 2)

    def test_create_order_invalid_method(self):
        with self.assertRaises(ValueError):
            self.client.get('/orders/create/')

    def test_create_order_missing_data(self):
        # Missing customer_name, should raise KeyError in view
        with self.assertRaises(KeyError):
            self.client.post('/orders/create/', {
                'customer_email': 'john@example.com',
                'product_ids': [self.product1.id],
                'quantities': [1]
            })

    def test_create_order_missing_product(self):
        # Using a product ID that doesn't exist
        with self.assertRaises(Product.DoesNotExist):
            self.client.post('/orders/create/', {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'product_ids': [999],
                'quantities': [1]
            })

    def test_create_order_empty_products(self):
        response = self.client.post('/orders/create/', {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'product_ids': [],
            'quantities': []
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.total_price, 0.00)
        order_products = OrderProduct.objects.filter(order=order)
        self.assertEqual(order_products.count(), 0)
