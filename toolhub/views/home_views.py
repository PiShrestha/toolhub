from django.shortcuts import render
from django.db.models import Q
from ..models import Item, Collection, BorrowRequest

def home(request):
    query = request.GET.get("q", "")
    items = Item.objects.all()
    collections = Collection.objects.all()

    # Filter by search query
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
        collections = collections.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # Anonymous users: only public collections and items in public collections or not in any collection
    if not request.user.is_authenticated:
        collections = collections.filter(visibility="public")
        items = items.filter(Q(collections__visibility="public") | Q(collections=None)).distinct()
    elif request.user.role == "librarian":
        pass  # Librarians see everything
    else:
        # Patrons: see all collections, but not items in private collections unless allowed
        collections = collections.exclude(visibility="private", allowed_users__isnull=True).distinct()

    # Set already_requested for each item
    for item in items:
        item.already_requested = False
        item.user_status = item.status_for_user(request.user)
        if request.user.is_authenticated and request.user.role == "patron":
            item.already_requested = BorrowRequest.objects.filter(
                item=item,
                user=request.user,
                status__in=["pending", "approved"]
            ).exists()

    return render(
        request,
        "toolhub/home/home.html",
        {"user": request.user, "items": items, "collections": collections, "query": query},
    )