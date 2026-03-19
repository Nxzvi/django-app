from django.shortcuts import render
from .models import Product
from django.core.paginator import Paginator
from django.db.models import Q

# Create your views here.


def list_products_view(request):
    search_query = request.GET.get('search', '').strip()

    print(search_query,"############# Searched ###############")
    filters = Q()
    if search_query:
        filters &= Q(name__icontains=search_query)

    active_products = Product.objects.filter(is_active=True, is_available=True).select_related('category').filter(filters)
    paginator = Paginator(active_products, 8)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'list-products.html', {'page_obj': page_obj})