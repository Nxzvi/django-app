from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from carts.views import merge_cart_cookie_to_user

# Create your views here.



def check_login(request):
    if request.method == 'POST' and 'login' in request.POST:
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            merge_cart_cookie_to_user(request, user)
            return redirect('product-list')
        else:
            messages.error(request, 'Invalid email or password')

    if request.POST and 'register' in request.POST:
        try:
            print(request.POST)
            username = request.POST.get('name')
            email = request.POST.get('email')
            password = request.POST.get('password')

            print(username, email, password, "######### Datas ############")
            user = User.objects.create_user(username=username, email=email, password=password)
            userProfile = UserProfile.objects.create(user=user)
            userProfile.name = username
            userProfile.phone = 8592888594
            userProfile.delete_status = UserProfile.live
            userProfile.save()

            user.is_active = True
            user.save()

            success_message = "User Successfully Registered login and Update Your Profile Details"
            messages.success(request, success_message)
            return redirect('user-login')
        except Exception as e:
            print(e, "Exception message ############################")
            error_message = "Username alredy exists"
            messages.error(request, error_message)

    return render(request, 'login-register.html')


def check_logout(request):
    logout(request)
    return redirect('product-list')