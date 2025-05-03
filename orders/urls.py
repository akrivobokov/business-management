from django.urls import path
from . import views

urlpatterns = [
    path('calculate/', views.calculate_order),
    path('create/', views.create_order),
]