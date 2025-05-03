from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(Product, through='OrderProduct')

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Logistics(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_time = models.IntegerField()