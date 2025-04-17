from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .forms import ProfilePictureForm, UserProfileForm, ItemForm, CollectionForm, PromoteUserForm
from django.core.exceptions import PermissionDenied
from .models import Item, Collection


# Create your views here.
@login_required
def home(request):
    items = Item.objects.all()
    collections = Collection.objects.all()

    print("DEBUG: Found items ->", items)

    if request.user.role == "librarian":
        return render(
            request,
            "toolhub/librarian_home.html",
            {"user": request.user, "items": items, "collections": collections},
        )
    return render(
        request,
        "toolhub/patron_home.html",
        {"user": request.user, "items": items, "collections": collections},
    )


@login_required
def logoutView(request):
    logout(request)
    return redirect("/")


@login_required
def profileView(request):
    return render(request, "toolhub/profile.html", {"user": request.user})


@login_required
def uploadPicture(request):
    if request.method == "POST":
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
    return render(request, "toolhub/profile_update.html", {"form": form})


@login_required
def add_item(request):
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can add items.")

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():

            form.save()

            return redirect("home")
    else:
        form = ItemForm()

    return render(request, "toolhub/add_item.html", {"form": form})


@login_required
def add_collection(request):
    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES)

        if request.user.role != "librarian":
            form.fields["visibility"].choices = [("public", "Public")]

        if form.is_valid():
            collection = form.save(commit=False)
            collection.creator = request.user
            collection.save()
            form.save_m2m()
            return redirect("home")
    else:
        form = CollectionForm()
        if request.user.role != "librarian":
            form.fields["visibility"].choices = [("public", "Public")]

    return render(request, "toolhub/add_collection.html", {"form": form})


@login_required
def view_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if collection.visibility == "private":
        is_librarian = request.user.role == "librarian"
        is_allowed_user = collection.allowed_users.filter(id=request.user.id).exists()

        if not (is_librarian or is_allowed_user or request.user == collection.creator):
            return redirect("access_denied")

    return render(
        request,
        "toolhub/view_collection.html",
        {
            "collection": collection,
            "items": collection.items.all(),
        },
    )


def access_denied(request):
    return render(request, "toolhub/access_denied.html")


@login_required
def edit_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if request.user != collection.creator:
        return redirect("access_denied")

    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES, instance=collection)

        if request.user.role != "librarian":
            form.fields["visibility"].choices = [("public", "Public")]

        if form.is_valid():
            form.save()
            return redirect("view_collection", collection_uuid=collection.uuid)
    else:
        form = CollectionForm(instance=collection)

        if request.user.role != "librarian":
            form.fields["visibility"].choices = [("public", "Public")]

    return render(
        request,
        "toolhub/edit_collection.html",
        {"form": form, "collection": collection},
    )


@login_required
def delete_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if request.user != collection.creator and request.user.role != "librarian":
        return redirect("access_denied")

    if request.method == "POST":
        collection.delete()
        return redirect("home")

    return redirect("edit_collection", collection_uuid=collection.uuid)

@login_required
def promote_user_view(request):
    if request.user.role != 'librarian':
        messages.error(request, "You are not authorized to promote users.")
        return redirect('home')

    if request.method == 'POST':
        form = PromoteUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                if user.role == 'librarian':
                    messages.info(request, f"{user.email} is already a librarian.")
                else:
                    user.role = 'librarian'
                    user.save()
                    messages.success(request, f"{user.email} has been promoted to librarian!")
            except CustomUser.DoesNotExist:
                messages.error(request, "User with that email does not exist.")
            return redirect('promote_user')  # reload page
    else:
        form = PromoteUserForm()

    return render(request, 'toolhub/promote_user.html', {'form': form})

@login_required
def borrow_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)

    if item.status == 'available':
        item.status = 'currently_borrowed'
        item.borrower = request.user
        item.save()

    return redirect('home')

@login_required
def return_item(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid)

    item.status = 'available'
    item.save()

    return redirect('home')