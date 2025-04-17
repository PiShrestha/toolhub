from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from ..forms import ProfilePictureForm, UserProfileForm

@login_required
def profile_view(request):
    return render(request, "toolhub/profile/profile.html", {"user": request.user})

@login_required
def upload_picture(request):
    if request.method == "POST":
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect("profile")
    else:
        form = ProfilePictureForm(instance=request.user)

    return render(request, "toolhub/profile/upload_picture.html", {"form": form})

@login_required
def clear_profile_picture(request):
    if request.method == "POST":
        if request.user.profile_picture:
            request.user.profile_picture.delete(save=False)
        request.user.profile_picture = None
        request.user.save()
        messages.success(request, "Your profile picture has been cleared.")
    return redirect("profile")

@login_required
def update_profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "toolhub/profile/profile_update.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    return redirect("/")