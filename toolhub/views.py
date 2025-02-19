from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def home(request):
    if request.user.is_staff:
        return render(request, "toolhub/librarian_home.html", {"user": request.user})
    return render(request, "toolhub/patron_home.html", {"user": request.user})

def logoutView(request):
    logout(request)
    return redirect("/")