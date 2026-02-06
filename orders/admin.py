from django.contrib import admin

from .models import (
    Banner,
    Invoice,
    InvoiceSequence,
    Logistics,
    Order,
    OrderProduct,
    PixelOrder,
    Product,
)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'cells', 'is_active', 'is_compliant', 'updated_at')
    list_filter = ('is_active', 'is_compliant')
    search_fields = ('title', 'target_url')


@admin.register(PixelOrder)
class PixelOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_type', 'cell_count', 'total_amount', 'status', 'created_at')
    list_filter = ('buyer_type', 'status', 'created_at')
    search_fields = ('full_name', 'organization_name', 'telegram_nick', 'phone', 'email')


admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(Logistics)
admin.site.register(Invoice)
admin.site.register(InvoiceSequence)
