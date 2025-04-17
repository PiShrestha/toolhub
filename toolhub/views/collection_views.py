from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ..models import Collection
from ..forms import CollectionForm

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

    return render(request, "toolhub/collections/add_collection.html", {"form": form})

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
        "toolhub/collections/view_collection.html",
        {"collection": collection, "items": collection.items.all()},
    )

@login_required
def edit_collection(request, collection_uuid):
    collection = get_object_or_404(Collection, uuid=collection_uuid)

    if not (request.user.role == "librarian" or request.user == collection.creator):
        return redirect('access_denied')

    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES, instance=collection)
        if form.is_valid():
            form.save()
            return redirect('view_collection', collection_uuid=collection.uuid)
    else:
        form = CollectionForm(instance=collection)

    return render(request, "toolhub/collections/edit_collection.html", {"form": form, "collection": collection})

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
def collections_page(request):
    """Display all collections with search functionality."""
    query = request.GET.get("q", "").strip()
    collections = Collection.objects.all()

    if query:
        collections = collections.filter(title__icontains=query)

    return render(request, "toolhub/collections/collections_page.html", {"collections": collections, "query": query})