from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db.models import Q
from ..forms import ProfilePictureForm, UserProfileForm

User = get_user_model()

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

@login_required
def search_users(request):
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can search and promote users.")

    query = request.GET.get("q", "").strip()
    users = []
    if query:
        users = User.objects.filter(
            Q(email__icontains=query) | Q(username__icontains=query)
        ).exclude(id=request.user.id)  # Prevent self-promotion

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        if user.role == "patron":
            user.role = "librarian"
            user.save()
            return redirect("search_users")
        elif user.role == "librarian":
            user.role = "patron"
            user.save()
            return redirect("search_users")

    return render(request, "toolhub/promote_user.html", {"users": users, "query": query})