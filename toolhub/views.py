from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .forms import ProfilePictureForm, UserProfileForm

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

@login_required
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

@login_required
def clear_profile_picture(request):
    if request.method == "POST":
        if request.user.profile_picture:
            request.user.profile_picture.delete(save=False)
        request.user.profile_picture = None
        request.user.save()
        messages.success(request, "Your profile picture has been cleared.")
    return redirect('profile')

@login_required
def update_profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "toolhub/profile_update.html", {"form": form})