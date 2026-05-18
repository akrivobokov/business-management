from django.core.exceptions import ValidationError
from django.db import models, transaction

FIELD_WIDTH_CELLS = 384
FIELD_HEIGHT_CELLS = 2160


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
    placement_x = models.PositiveIntegerField(
        default=0,
        help_text='X (в ячейках 10x10) от левого края',
    )
    placement_y = models.PositiveIntegerField(
        default=0,
        help_text='Y (в ячейках 10x10) от верхнего края',
    )
    placement_width = models.PositiveIntegerField(
        default=1,
        help_text='Ширина (в ячейках 10x10)',
    )
    placement_height = models.PositiveIntegerField(
        default=1,
        help_text='Высота (в ячейках 10x10)',
    )
    is_active = models.BooleanField(default=True)
    is_compliant = models.BooleanField(
        default=False,
        help_text='Подтверждение администратора, что баннер и ссылка соответствуют законодательству РФ.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.placement_width <= 0 or self.placement_height <= 0:
            raise ValidationError('Размеры баннера должны быть больше нуля.')
        if self.placement_x + self.placement_width > FIELD_WIDTH_CELLS:
            raise ValidationError('Баннер выходит за пределы поля по ширине.')
        if self.placement_y + self.placement_height > FIELD_HEIGHT_CELLS:
            raise ValidationError('Баннер выходит за пределы поля по высоте.')
        expected_cells = self.placement_width * self.placement_height
        if self.cells != expected_cells:
            raise ValidationError('Количество ячеек должно совпадать с площадью баннера.')


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
    placement_x = models.PositiveIntegerField(default=0)
    placement_y = models.PositiveIntegerField(default=0)
    placement_width = models.PositiveIntegerField(default=1)
    placement_height = models.PositiveIntegerField(default=1)
    personal_data_consent = models.BooleanField(default=False)

    total_amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, default='new')
    telegram_status = models.CharField(max_length=20, default='pending')
    telegram_attempts = models.PositiveIntegerField(default=0)
    telegram_error = models.TextField(blank=True)
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
