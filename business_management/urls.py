from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.landing),
    path('api/pixel-order/', views.create_pixel_order, name='create_pixel_order'),
    path('business-calculator/', views.business_calculator, name='business_calculator'),
    path('admin/', admin.site.urls),
    path('orders/', include('orders.urls')),
]
