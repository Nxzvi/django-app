from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from .models import Coupon
from carts.models import Cart
from accounts.models import UserProfile


def validate_coupon(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthenticated', 'message': 'Please log in to apply coupon.'}, status=403)

    code = request.GET.get('code', '').strip()

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'status': 'invalid', 'message': 'Coupon does not exist.'})

    if coupon.expiry < timezone.now():
        return JsonResponse({'status': 'expired', 'message': 'Coupon has expired.'})
    if coupon.used_counts >= coupon.limit:
        return JsonResponse({'status': 'limit_reached', 'message': 'Coupon usage limit reached.'})
    if coupon.active_status != Coupon.live:
        return JsonResponse({'status': 'inactive', 'message': 'Coupon is not active.'})

    user_profile = UserProfile.objects.get(user=request.user)

    try:
        cart = Cart.objects.get(user=user_profile, is_checkedout=False)
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'empty_cart', 'message': 'Your cart is empty or already checked out.'})

    cart_items = cart.cart_items.select_related('product', 'product__category')
    if not cart_items.exists():
        return JsonResponse({'status': 'empty_cart', 'message': 'Your cart has no items.'})

    eligible_products = coupon.applicable_products.all()
    eligible_categories = coupon.applicable_categories.all()

    total_discount = Decimal('0.00')
    eligible_found = False
    applied_product_names = []

    for item in cart_items:
        product = item.product
        if not product:
            continue

        is_eligible = False

        if eligible_products.exists() and product in eligible_products:
            is_eligible = True
        elif eligible_categories.exists() and product.category in eligible_categories:
            is_eligible = True

        if is_eligible:
            eligible_found = True
            applied_product_names.append(product.name)
            original_total = product.price * item.quantity

            if coupon.discount_type == Coupon.PERCENTAGE:
                discount = original_total * (coupon.discount / 100)
            else:
                discount = coupon.discount * item.quantity

            discount = min(discount, original_total)
            total_discount += discount

    if not eligible_found:
        return JsonResponse({'status': 'not_applicable', 'message': 'Coupon is not applicable to any items in your cart.'})
    
    request.session['applied_coupon'] = {
        'code': coupon.code,
        'discount_amount': float(total_discount.quantize(Decimal('0.01')))
    }

    request.session.modified = True

    return JsonResponse({
        'status': 'valid',
        'message': f"Coupon applied successfully to: {', '.join(applied_product_names)}.",
        'discount_amount': float(total_discount.quantize(Decimal('0.01'))),
        'applied_products': applied_product_names
    })



def clear_coupon(request):
    request.session.pop('applied_coupon', None)
    request.session.modified = True
    print("############ Session Cleared ##################")
    return JsonResponse({'status': 'cleared'})