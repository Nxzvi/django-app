from django.db import models
from accounts.models import UserProfile
from products.models import Product


class Cart(models.Model):

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='carts', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_checkedout = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id) + "----" + str(self.user_id)


class CartItems(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='products')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return str(self.cart.id) + "----" + str(self.cart.user.name)+ "----" + str(self.product_id)+ "----" + str(self.quantity)


class Order(models.Model):

    ORDER_PROCESSING = 0
    ORDER_CONFIRMED = 1
    ORDER_DELIVERED = 2
    ORDER_CANCEL_REQUESTED = 3
    ORDER_CANCELED = 4
    order_status = ((ORDER_CONFIRMED, 'order_confirmed'),(ORDER_PROCESSING, 'order_processing'),
                    (ORDER_DELIVERED, 'order_delivered'), (ORDER_CANCEL_REQUESTED, 'order_cancel_requested'),
                    (ORDER_CANCELED, 'order_canceled'))

    COD = 1
    PAY_NOW = 2
    pay_mode = ((PAY_NOW, 'pay_now'), (COD, 'cod'))

    PENDING = 1
    PARTIAL_PAY = 2
    FULL_PAY = 3
    pay_status = ((PENDING, 'pending'), (PARTIAL_PAY, 'partial_pay'), (FULL_PAY, 'fully_pay'))

    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='orders')

    order_stage = models.IntegerField(choices=order_status, default=ORDER_PROCESSING)
    payment_mode = models.IntegerField(choices=pay_mode, default=0, null=True)
    payment_status = models.IntegerField(choices=pay_status, default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    transaction_id = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.id}----{self.user.name if self.user else 'No User'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) {self.order.id}"