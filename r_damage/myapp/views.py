import os
 
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
 
from .models import *
 
# -------------------------------------------------
# LOGIN CHECK
# -------------------------------------------------
 
def require_login(request, redirect_url="/login"):
    if "lid" not in request.session:
        messages.error(request, "Please login first")
        return redirect(redirect_url)
    return None
 
 
def require_admin(request, redirect_url="/login"):
 
    check = require_login(request, redirect_url)
    if check:
        return check
 
    if request.session.get("usertype") != "Admin":
        messages.error(request, "Admin access required")
        return redirect("/dashboard")
 
    return None
 
# -------------------------------------------------
# INDEX
# -------------------------------------------------
 
def index(request):
    logout(request)
    return render(request, "index.html")
 
# -------------------------------------------------
# LOGIN
# -------------------------------------------------
 
def login_view(request):
 
    if request.method == "POST":
 
        username = request.POST.get("username")
        password = request.POST.get("password")
 
        user = authenticate(
            request,
            username=username,
            password=password
        )
 
        if user:
 
            login(request, user)
            request.session["lid"] = user.id
            request.session["usertype"] = user.usertype
            request.session["username"] = user.username
 
            if user.usertype == "Admin":
                return redirect("/admin_home")
 
            return redirect("/dashboard")
 
        messages.error(request, "Invalid username or password")
        return redirect("/login")
 
    return render(request, "login.html")
 
 
def signout(request):
    logout(request)
    request.session.flush()
    return redirect("/")
 
# -------------------------------------------------
# REGISTRATION
# -------------------------------------------------
 
def register_view(request):
 
    if request.method == "POST":
 
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
 
        if not username or not password:
            messages.error(request, "Username and password are required")
            return redirect("/register")
 
        if Login.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("/register")
 
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("/register")
 
        login_obj = Login.objects.create_user(
            username=username,
            email=request.POST.get("email"),
            password=password,
            usertype="User",
            viewpassword=password
        )
 
        UserProfile.objects.create(
            user=login_obj,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address")
        )
 
        messages.success(request, "Registration successful. Please log in")
        return redirect("/login")
 
    return render(request, "register.html")


# -------------------------------------------------
# USER DASHBOARD & REPORTING
# -------------------------------------------------
 
def user_home(request):
    return render(request, "USER/home.html")

def admin_home(request):
    return render(request, "ADMIN/home.html")
 