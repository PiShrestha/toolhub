from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .forms import ProfilePictureForm

# Create your views here.
@login_required
def home(request):
    if request.user.role == 'librarian':
        return render(request, "toolhub/librarian_home.html", {"user": request.user})
    return render(request, "toolhub/patron_home.html", {"user": request.user})

@login_required
def logoutView(request):
    logout(request)
    return redirect("/")

@login_required
def profileView(request):
    return render(request, "toolhub/profile.html", {"user": request.user})

def uploadPicture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect("profile")
        
    else:
        form = ProfilePictureForm(instance=request.user)
    
    return render(request, "toolhub/upload_picture.html", {"form": form})