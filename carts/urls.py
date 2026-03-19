"""
URL configuration for cuppon_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from carts import views

urlpatterns = [
    path('cart/', views.cart_view, name='user-cart'),
    path('get-cart-items/', views.get_user_cart_items, name='get-cart-items'),
    path('update-cart-item/', views.update_cart_item_quantity, name='update-cart-item'),
    path('remove-cart-item/', views.remove_cart_item, name='remove-cart-item'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('proceed-to-checkout/', views.proceed_to_checkout, name="proceed-to-checkout"),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.list_orders, name='orders'),
]
