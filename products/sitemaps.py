from django.contrib.sitemaps import Sitemap
from .models import Product, Category

class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Product.objects.filter(available=True)

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        from django.urls import reverse
        return reverse('products:product_detail', args=[obj.id, obj.slug])

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        from django.urls import reverse
        return reverse('products:product_list_by_category', args=[obj.slug])
