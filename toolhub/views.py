from django.shortcuts import render, redirect
from django.contrib.auth import logout 

# Create your views here.

def home(request):
    return render(request, "toolhub/home.html")

def logoutView(request):
    logout(request)
    return redirect("/toolhub/")