from django.http import JsonResponse
from .models import Product, Order, OrderProduct, Logistics
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def calculate_order(request):
    if request.method == 'POST':
        data = request.POST
        product_ids = data.getlist('product_ids')
        quantities = data.getlist('quantities')
        total_price = 0
        order_products = []

        for pid, qty in zip(product_ids, quantities):
            product = Product.objects.get(id=pid)
            total_price += product.price * int(qty)
            order_products.append({'product': product.name, 'quantity': qty})

        logistics = Logistics.objects.filter(product__in=product_ids)
        delivery_cost = sum([l.delivery_cost for l in logistics])
        total_price += delivery_cost

        return JsonResponse({'total_price': total_price, 'delivery_cost': delivery_cost, 'items': order_products})

@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        data = request.POST
        customer_name = data['customer_name']
        customer_email = data['customer_email']
        products = data.getlist('product_ids')
        quantities = data.getlist('quantities')

        order = Order.objects.create(customer_name=customer_name, customer_email=customer_email, total_price=0)
        total_price = 0
        for pid, qty in zip(products, quantities):
            product = Product.objects.get(id=pid)
            total_price += product.price * int(qty)
            OrderProduct.objects.create(order=order, product=product, quantity=qty)

        order.total_price = total_price
        order.save()
        return JsonResponse({'message': 'Order created', 'order_id': order.id})