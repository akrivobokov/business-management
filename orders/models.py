from django.db import models, transaction


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


class Banner(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField()
    target_url = models.URLField()
    cells = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_compliant = models.BooleanField(
        default=False,
        help_text='Подтверждение администратора, что баннер и ссылка соответствуют законодательству РФ.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PixelOrder(models.Model):
    INDIVIDUAL = 'individual'
    LEGAL = 'legal'
    BUYER_TYPES = [
        (INDIVIDUAL, 'Физлицо'),
        (LEGAL, 'Юрлицо/ИП'),
    ]

    buyer_type = models.CharField(max_length=20, choices=BUYER_TYPES)
    full_name = models.CharField(max_length=255, blank=True)
    telegram_nick = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)

    organization_name = models.CharField(max_length=255, blank=True)
    inn = models.CharField(max_length=12, blank=True)
    email = models.EmailField(blank=True)

    banner_image_url = models.URLField()
    banner_target_url = models.URLField()
    cell_count = models.PositiveIntegerField()
    personal_data_consent = models.BooleanField(default=False)

    total_amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Заявка #{self.pk} ({self.get_buyer_type_display()})'


class InvoiceSequence(models.Model):
    last_number = models.PositiveIntegerField(default=0)

    @classmethod
    def next_number(cls):
        with transaction.atomic():
            sequence, _ = cls.objects.select_for_update().get_or_create(pk=1)
            sequence.last_number += 1
            sequence.save(update_fields=['last_number'])
            return f'НП{sequence.last_number:05d}'


class Invoice(models.Model):
    order = models.OneToOneField(PixelOrder, on_delete=models.CASCADE, related_name='invoice')
    number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number
