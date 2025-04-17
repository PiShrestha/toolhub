from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import Item, Collection

@login_required
def home(request):
    query = request.GET.get("q", "")
    
    # Filter items and collections based on the query
    items = Item.objects.all()
    collections = Collection.objects.all()

    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
        collections = collections.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    if request.user.role == "librarian":
        # Librarian: Show all items and collections
        pass
    else:
        # Patron: Show only public collections and available items
        collections = collections.filter(visibility="public")
        items = items.filter(status="available")

    return render(
        request,
        "toolhub/home/home.html",
        {"user": request.user, "items": items, "collections": collections, "query": query},
    )