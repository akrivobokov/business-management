from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render  # 👈 нужно для рендера шаблона

def landing(request):
    return render(request, 'landing.html')  # 👈 обработка /

urlpatterns = [
    path('', landing),  # 👈 главная страница сайта
    path('admin/', admin.site.urls),
    path('orders/', include('orders.urls')),
]
