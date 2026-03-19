from django.db import models
from accounts.models import UserProfile
from products.models import Product, Category
from carts.models import Order, OrderItem


class Coupon(models.Model):

    live = 1
    finished = 0
    coupon_status = ((live, 'Live'), (finished, 'finished'))

    PERCENTAGE = 'percentage'
    FIXED = 'fixed'
    DISCOUNT_TYPE_CHOICES = ((PERCENTAGE, 'Percentage'),(FIXED, 'Fixed'),)

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    discount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=FIXED)
    expiry = models.DateTimeField()
    limit = models.PositiveIntegerField()
    used_counts = models.PositiveIntegerField(default=0)
    active_status =  models.IntegerField(choices=coupon_status, default=live)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    applicable_products = models.ManyToManyField(Product, blank=True, related_name='coupons')
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='coupons')


    def __str__(self):
        return self.name +"----"+ self.code
    

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='used_coupons')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_usages', null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'user', 'order')