from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ..models import Collection, BorrowRequest
from ..forms import CollectionForm

@login_required
def add_collection(request):
    if request.method == "POST":
        print(request.POST)
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

    return render(request, "toolhub/collections/add_collection.html", {"form": form})

def view_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)
    # Restrict access to private collections for anonymous users and unauthorized patrons
    if collection.visibility == "private":
        is_librarian = request.user.is_authenticated and request.user.role == "librarian"
        is_allowed_user = request.user.is_authenticated and collection.allowed_users.filter(id=request.user.id).exists()
        is_creator = request.user.is_authenticated and request.user == collection.creator
        if not (is_librarian or is_allowed_user or is_creator):
            return redirect("access_denied")

    # Add already_requested logic for items in the collection
    items = collection.items.all()
    for item in items:
        item.already_requested = False
        if request.user.is_authenticated:
            item.already_requested = BorrowRequest.objects.filter(
                item=item,
                user=request.user,
                status__in=["pending", "approved"]
            ).exists()

    return render(
        request,
        "toolhub/collections/view_collection.html",
        {"collection": collection, "items": items},
    )

@login_required
def edit_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if not (request.user.role == "librarian" or request.user == collection.creator):
        return redirect('access_denied')

    if request.method == "POST":
        print(request.POST)  # DEBUG
        form = CollectionForm(request.POST, request.FILES, instance=collection)
        if form.is_valid():
            collection = form.save(commit=False)

            # Update items and allowed_users before saving
            if "items" in request.POST:
                collection.items.set(form.cleaned_data.get("items", []))
            else:
                collection.items.clear()

            if "allowed_users" in request.POST:
                collection.allowed_users.set(form.cleaned_data.get("allowed_users", []))
            else:
                collection.allowed_users.clear()

            collection.save()  # Save the collection after updating relationships
            return redirect("view_collection", collection_uuid=str(collection.uuid))
        else:
            print("Form errors:", form.errors)  # DEBUG
    else:
        form = CollectionForm(instance=collection)

    return render(request, "toolhub/collections/edit_collection.html", {
        "form": form,
        "collection": collection,
    })

@login_required
def delete_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if request.user != collection.creator and request.user.role != "librarian":
        return redirect("access_denied")

    if request.method == "POST":
        collection.delete()
        return redirect("home")

    return redirect("edit_collection", collection_uuid=collection.uuid)

def collections_page(request):
    """Display all collections with search functionality."""
    query = request.GET.get("q", "")
    collections = Collection.objects.all()
    if query:
        collections = collections.filter(title__icontains=query)
    # Only show public collections to anonymous users
    if not request.user.is_authenticated:
        collections = collections.filter(visibility="public")

    # Add already_requested logic for items in each collection
    for collection in collections:
        for item in collection.items.all():
            item.already_requested = False
            if request.user.is_authenticated:
                item.user_status = item.status_for_user(request.user)
                item.already_requested = BorrowRequest.objects.filter(
                    item=item,
                    user=request.user,
                    status__in=["pending", "approved"]
                ).exists()

    return render(request, "toolhub/collections/collections_page.html", {"collections": collections, "query": query})