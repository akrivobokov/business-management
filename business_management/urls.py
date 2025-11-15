from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.landing),  # 👈 главная страница сайта
    path('business-calculator/', views.business_calculator, name='business_calculator'),
    path('admin/', admin.site.urls),
    path('orders/', include('orders.urls')),
]
