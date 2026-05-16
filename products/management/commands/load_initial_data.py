from django.core.management.base import BaseCommand
from products.models import Category, Product
from django.utils.text import slugify
from unidecode import unidecode
import random

class Command(BaseCommand):
    help = 'Load initial data for categories and products'

    def handle(self, *args, **kwargs):
        categories_data = [
            'Мороженое',
            'Пельмени',
            'Овощи и ягоды',
            'Картофель',
            'Вареники',
            'Мясо птицы',
            'Готовые блюда',
            'Горячие штучки',
            'Пицца и тесто',
            'Блины',
            'Морепродукты',
            'Котлеты и наггетсы',
        ]

        products_data = [
            {'name': 'Пломбир ванильный', 'category_name': 'Мороженое', 'price': '150.00', 'sku': 'ICE-001'},
            {'name': 'Эскимо шоколадное', 'category_name': 'Мороженое', 'price': '120.00', 'sku': 'ICE-002'},
            {'name': 'Пельмени Сибирские', 'category_name': 'Пельмени', 'price': '350.00', 'sku': 'PEL-001'},
            {'name': 'Смесь овощная Гавайская', 'category_name': 'Овощи и ягоды', 'price': '210.00', 'sku': 'VEG-001'},
            {'name': 'Клубника замороженная', 'category_name': 'Овощи и ягоды', 'price': '450.00', 'sku': 'BER-001'},
            {'name': 'Картофель фри 9мм', 'category_name': 'Картофель', 'price': '280.00', 'sku': 'POT-001'},
            {'name': 'Чебупели с мясом', 'category_name': 'Горячие штучки', 'price': '190.00', 'sku': 'HOT-001'},
            {'name': 'Пицца Маргарита', 'category_name': 'Пицца и тесто', 'price': '300.00', 'sku': 'PIZ-001'},
            {'name': 'Блины с мясом', 'category_name': 'Блины', 'price': '220.00', 'sku': 'BLI-001'},
            {'name': 'Креветки очищенные', 'category_name': 'Морепродукты', 'price': '950.00', 'sku': 'SEA-001'},
            {'name': 'Наггетсы куриные', 'category_name': 'Котлеты и наггетсы', 'price': '260.00', 'sku': 'NUG-001'},
        ]

        for cat_name in categories_data:
            slug = slugify(unidecode(cat_name))
            category, created = Category.objects.get_or_create(name=cat_name, defaults={'slug': slug})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        for prod_data in products_data:
            try:
                category = Category.objects.get(name=prod_data['category_name'])
                slug = slugify(unidecode(prod_data['name']))
                # appending random string if slug exists, just to avoid errors on duplicate loads

                product, created = Product.objects.get_or_create(
                    sku=prod_data['sku'],
                    defaults={
                        'name': prod_data['name'],
                        'slug': slug,
                        'category': category,
                        'price': prod_data['price'],
                        'description': f"Вкусный продукт: {prod_data['name']}",
                        'available': True,
                    }
                )
                if created:
                     self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Category {prod_data['category_name']} does not exist!"))

        self.stdout.write(self.style.SUCCESS('Successfully loaded initial data'))
