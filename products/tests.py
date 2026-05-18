from django.test import TestCase
from django.urls import reverse
from .models import Category, Product

class ProductAppTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Мороженое', slug='morozhenoe')
        self.product = Product.objects.create(
            category=self.category,
            name='Пломбир',
            slug='plombir',
            price='100.00',
            sku='ICE-001',
            available=True
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Мороженое')
        self.assertEqual(str(self.category), 'Мороженое')

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Пломбир')
        self.assertEqual(str(self.product), 'Пломбир')
        self.assertTrue(self.product.available)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Мороженое')

    def test_product_list_view(self):
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_list.html')
        self.assertContains(response, 'Пломбир')

    def test_product_list_by_category_view(self):
        response = self.client.get(reverse('products:product_list_by_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_list.html')
        self.assertContains(response, 'Пломбир')

    def test_product_detail_view(self):
        response = self.client.get(reverse('products:product_detail', args=[self.product.id, self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertContains(response, 'Пломбир')
        self.assertContains(response, '100.00')

    def test_sitemap(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.slug)
