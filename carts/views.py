from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Cart, CartItems
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
import json
from products.models import Product
from decimal import Decimal
from cuppons.models import Coupon, CouponUsage
from carts.models import Order, OrderItem
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.contrib import messages




def cart_view(request):
    return render(request, 'cart.html')


def get_user_cart_items(request):
    # If user is authenticated → get cart from DB
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            cart = Cart.objects.get(user=user_profile, is_checkedout=False)
        except (UserProfile.DoesNotExist, Cart.DoesNotExist):
            return JsonResponse({'message': 'No active cart found.'}, status=404)

        cart_items = cart.cart_items.select_related('product').all()

        if not cart_items:
            return JsonResponse({'message': 'No items in the cart.'}, status=404)

        items_data = []
        for item in cart_items:
            if item.product:
                items_data.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price_per_unit': float(item.product.price),
                })

        return JsonResponse({
            'cart_id': cart.id,
            'user': user_profile.name,
            'items': items_data,
        }, status=200)

    # If user is not authenticated → get cart from cookies
    else:
        guest_cart = request.COOKIES.get('guest_cart')
        try:
            guest_cart_data = json.loads(guest_cart) if guest_cart else {}
        except json.JSONDecodeError:
            guest_cart_data = {}

        if not guest_cart_data:
            return JsonResponse({'message': 'No items in the guest cart.'}, status=404)

        items_data = []
        for product_id, details in guest_cart_data.items():
            try:
                product = Product.objects.get(id=product_id)
                items_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity': details['quantity'],
                    'price_per_unit': float(product.price),
                })
            except Product.DoesNotExist:
                continue  # Skip if product was deleted

        return JsonResponse({
            'cart_id': None,
            'user': 'Guest',
            'items': items_data,
        }, status=200)

@csrf_exempt
def update_cart_item_quantity(request):
    print("############### In update_cart_item_quantity ########################")
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = str(data.get("item_id"))
        new_quantity = int(data.get("quantity", 1))
        cart_id = data.get("cart_id")

        # For logged-in users
        if request.user.is_authenticated:
            try:
                item = CartItems.objects.filter(product=product_id, cart=cart_id).first()
                if item:
                    item.quantity = new_quantity
                    item.save()
                    return JsonResponse({'message': 'Quantity updated.'})
                else:
                    return JsonResponse({'error': 'Item not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        # For guest users — update cookie cart
        else:
            guest_cart = request.COOKIES.get('guest_cart')
            try:
                guest_cart_data = json.loads(guest_cart) if guest_cart else {}
            except json.JSONDecodeError:
                guest_cart_data = {}

            if product_id in guest_cart_data:
                guest_cart_data[product_id]['quantity'] = new_quantity
                response = JsonResponse({'message': 'Guest cart quantity updated.'})
                response.set_cookie(
                    'guest_cart',
                    json.dumps(guest_cart_data),
                    max_age=7 * 24 * 60 * 60,
                    httponly=False,
                    samesite='Lax'
                )
                return response
            else:
                return JsonResponse({'error': 'Item not found in guest cart.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def remove_cart_item(request):
    print("############### In remove_cart_item ########################")
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = str(data.get("item_id"))  # Keep as string for consistency
        cart_id = data.get("cart_id")

        # If user is authenticated, remove from DB
        if request.user.is_authenticated:
            try:
                item = CartItems.objects.filter(product=product_id, cart=cart_id).first()
                if item:
                    item.delete()
                    return JsonResponse({'message': 'Item removed.'})
                else:
                    return JsonResponse({'error': 'Item not found.'}, status=404)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        # If user is not authenticated, remove from guest cart (cookie)
        else:
            guest_cart = request.COOKIES.get('guest_cart')
            try:
                guest_cart_data = json.loads(guest_cart) if guest_cart else {}
            except json.JSONDecodeError:
                guest_cart_data = {}

            if product_id in guest_cart_data:
                del guest_cart_data[product_id]
                response = JsonResponse({'message': 'Item removed from guest cart.'})
                response.set_cookie(
                    'guest_cart',
                    json.dumps(guest_cart_data),
                    max_age=7 * 24 * 60 * 60,
                    httponly=False,
                    samesite='Lax'
                )
                return response
            else:
                return JsonResponse({'error': 'Item not found in guest cart.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = str(data.get("product_id"))  # keep as string for JSON
        quantity = int(data.get("quantity", 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'message': 'Product not found.'}, status=404)

        # If user is authenticated
        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)

                cart, _ = Cart.objects.get_or_create(user=user_profile, is_checkedout=False)

                cart_item, created = CartItems.objects.get_or_create(cart=cart, product=product)
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
                    return JsonResponse({'message': 'Item quantity updated in cart successfully.'})
                return JsonResponse({'message': 'Item added to cart successfully.'})

            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)

        # If user is not authenticated, save to cookies
        else:
            guest_cart = request.COOKIES.get('guest_cart')
            try:
                guest_cart_data = json.loads(guest_cart) if guest_cart else {}
            except json.JSONDecodeError:
                guest_cart_data = {}

            # Update or add the product
            if product_id in guest_cart_data:
                guest_cart_data[product_id]['quantity'] += quantity
            else:
                guest_cart_data[product_id] = {'quantity': quantity}

            response = JsonResponse({'message': 'Item added to guest cart.'})
            response.set_cookie(
                'guest_cart',
                json.dumps(guest_cart_data),
                max_age=7*24*60*60,  # 1 week
                httponly=False,
                samesite='Lax'
            )
            return response

    return JsonResponse({'message': 'Invalid request method.'}, status=400)


@login_required
def proceed_to_checkout(request):

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        cart = Cart.objects.get(user=user_profile, is_checkedout=False)
        cart_items_qs = cart.cart_items.select_related('product', 'product__category', 'cart__user').all()

        if not cart_items_qs.exists():
            return render(request, 'checkout.html', {
                'message': 'Your cart is empty.'
            })

        subtotal = Decimal('0.00')
        cart_items = []

        for item in cart_items_qs:
            item_subtotal = item.product.price * item.quantity
            subtotal += item_subtotal

            cart_items.append({
                'id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'item_subtotal': item_subtotal,
            })

        coupon_data = request.session.get('applied_coupon')
        discount = Decimal(str(coupon_data.get('discount_amount', 0))) if coupon_data else Decimal('0.00')
        coupon_code = coupon_data.get('code') if coupon_data else None

        total = subtotal - discount
        total = max(total, Decimal('0.00'))

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
            'coupon_code': coupon_code,
        }

        # Print context to terminal
        print("\n--- Proceed to Checkout Context ---")
        for key, value in context.items():
            print(f"{key}: {value}")
        print("----------------------------------\n")

        return render(request, 'checkout.html', context)

    except Cart.DoesNotExist:
        return render(request, 'checkout.html', {
            'message': 'No active cart found.'
        })


@login_required
def checkout_view(request):
    if request.method != 'POST':

        messages.error(request, 'Invalid request method.')
        return redirect('checkout')

    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to place an order.')
        return redirect('checkout')

    payment_method = request.POST.get('payment-method')
    pay_type = request.POST.get('pay-type')
    payment_method_type = request.POST.get('payment-method-type')
    transaction_id = request.POST.get('transaction-id')
    payment_amount = request.POST.get('payment-amount')

    print(pay_type,"###########################################")

    if payment_method == 'pay-now' and not all([pay_type, payment_method_type, transaction_id, payment_amount]):
        messages.error(request, 'Incomplete payment details for online payment.')
        return redirect('checkout')

    if not payment_method:
        messages.error(request, 'You must select a payment option to place an order.')
        return redirect('checkout')

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        cart = Cart.objects.get(user=user_profile, is_checkedout=False)
        cart_items = cart.cart_items.select_related('product')

        if not cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('checkout')

        subtotal = sum([item.product.price * item.quantity for item in cart_items])

        coupon_data = request.session.get('applied_coupon')
        discount = Decimal(str(coupon_data.get('discount_amount', 0))) if coupon_data else Decimal('0.00')
        coupon_code = coupon_data.get('code') if coupon_data else None

        total = max(subtotal - discount, Decimal('0.00'))

        if payment_method == 'cash-on-delivery':
            payment_mode = Order.COD
            payment_status = Order.PENDING
            payed_amount = Decimal('0.00')
        else:
            payment_mode = Order.PAY_NOW
            if pay_type == 'pay-advance' and int(payment_amount) < total:
                payment_status = Order.PARTIAL_PAY
            elif pay_type == 'pay-advance' and int(payment_amount) >= total:
                payment_status = Order.FULL_PAY
            else:
                payment_status = Order.FULL_PAY
            try:
                payed_amount = Decimal(payment_amount)
                if pay_type == 'pay-fully' and payed_amount != total:
                    messages.error(request, 'Invalid full amount payed.')
                    return redirect('checkout')
            except Exception:
                messages.error(request, 'Invalid amount entered.')
                return redirect('checkout')

        order = Order.objects.create(
            user=user_profile,
            order_stage=Order.ORDER_PROCESSING,
            payment_mode=payment_mode,
            payment_status=payment_status,
            order_amount=total,
            payed_amount=payed_amount,
            transaction_id=transaction_id if payment_mode == Order.PAY_NOW else None
        )

        if coupon_code:
            try:
                applied_coupon = Coupon.objects.get(code=coupon_code)
                if applied_coupon:
                    eligible_products = applied_coupon.applicable_products.all() if applied_coupon else []
                    eligible_categories = applied_coupon.applicable_categories.all() if applied_coupon else []
            except Coupon.DoesNotExist:
                applied_coupon = None

        is_coupon_applied = False

        for item in cart_items:
            product = item.product
            original_price = product.price
            discounted_price = original_price

            if coupon_code:
                if applied_coupon:
                    is_eligible = False
                    if eligible_products.exists() and product in eligible_products:
                        is_eligible = True
                    elif eligible_categories.exists() and product.category in eligible_categories:
                        is_eligible = True

                    if is_eligible:
                        is_coupon_applied = True
                        if applied_coupon.discount_type == Coupon.PERCENTAGE:
                            discount = original_price * (applied_coupon.discount / 100)
                        else:
                            discount = applied_coupon.discount

                        discount = min(discount, original_price)
                        discounted_price = original_price - discount

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                unit_price=discounted_price.quantize(Decimal('0.01'))
            )

        if is_coupon_applied:
            CouponUsage.objects.create(
                coupon=applied_coupon,
                user=user_profile,
                order=order
            )

            applied_coupon.used_counts += 1
            applied_coupon.save()

        cart.is_checkedout = True
        cart.save()

        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']

        # return JsonResponse({'message': 'Order placed successfully.', 'total': float(total)})
        messages.success(request, 'Order placed successfully.')
        return redirect('orders')

    except Cart.DoesNotExist:
        # return JsonResponse({'error': 'No active cart found.'}, status=404)
        messages.error(request, 'No active cart found.')
        return redirect('checkout')

    except Exception as e:
        print(f"[Checkout Error] {str(e)}")
        # return JsonResponse({'error': 'An unexpected error occurred during checkout.'}, status=500)
        messages.error(request, 'An unexpected error occurred during checkout.')
        return redirect('checkout')


@login_required
def list_orders(request):
    order_stage_filter = [int(val) for val in request.GET.getlist('order_stage') if val.isdigit()]
    payment_mode_filter = [int(val) for val in request.GET.getlist('payment_mode') if val.isdigit()]
    payment_status_filter = [int(val) for val in request.GET.getlist('payment_status') if val.isdigit()]
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    sort_by = request.GET.get('sort')

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except AttributeError:
        return HttpResponseForbidden("User profile not found.")

    filters = Q(user=user_profile)
    
    if order_stage_filter:
        filters &= Q(order_stage__in=order_stage_filter)
    if payment_mode_filter:
        filters &= Q(payment_mode__in=payment_mode_filter)
    if payment_status_filter:
        filters &= Q(payment_status__in=payment_status_filter)

    orders = Order.objects.prefetch_related('order_items__product', 'user').filter(filters)

    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)

    # Sorting
    if sort_by == 'latest':
        orders = orders.order_by('-created_at')
    elif sort_by == 'oldest':
        orders = orders.order_by('created_at')
    elif sort_by == 'lowest':
        orders = orders.order_by('order_amount')
    elif sort_by == 'highest':
        orders = orders.order_by('-order_amount')
    else:
        orders = orders.order_by('-created_at')  # Default sort

    # Prepare order data
    order_data = []
    for order in orders:
        items = [
            f"{item.product.name} (x{item.quantity})"
            for item in order.order_items.all()
        ]

        balance_amount = (order.order_amount or 0) - (order.payed_amount or 0)

        order_data.append({
            'id': order.id,
            'user': order.user.name if order.user else 'No User',
            'order_stage': order.get_order_stage_display(),
            'payment_mode': order.get_payment_mode_display(),
            'payment_status': order.get_payment_status_display(),
            'order_amount': order.order_amount,
            'payed_amount': order.payed_amount,
            'balance_amount': round(balance_amount, 2),
            'items': items,
            'date': order.created_at.strftime('%d-%m-%Y'),
        })

    paginator = Paginator(order_data, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'active_filters': {
            'order_stage': order_stage_filter,
            'payment_mode': payment_mode_filter,
            'payment_status': payment_status_filter,
        },
        'order_stage_choices': Order.order_status,
        'payment_mode_choices': Order.pay_mode,
        'payment_status_choices': Order.pay_status,
    }

    return render(request, 'orders.html', context)



def merge_cart_cookie_to_user(request, user):
    """
    Call this function right after user logs in.
    :param request: Django request object
    :param user: authenticated user
    """
    guest_cart = request.COOKIES.get('guest_cart')
    if not guest_cart:
        return  # No guest cart to merge

    try:
        guest_cart_data = json.loads(guest_cart)
    except json.JSONDecodeError:
        return  # Invalid cookie, skip merging

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return  # Shouldn’t happen, but safety first

    cart, _ = Cart.objects.get_or_create(user=user_profile, is_checkedout=False)

    for product_id, item_data in guest_cart_data.items():
        quantity = int(item_data.get("quantity", 1))
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue  # Skip deleted or invalid products

        cart_item, created = CartItems.objects.get_or_create(cart=cart, product=product)
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity  # update quantity if already exists
        cart_item.save()

    print("################### Clearing the cookies ##################")
    # Clear the guest cart cookie after merging
    request.COOKIES.pop('guest_cart', None)
    print("################### Cookies cleared ##################")