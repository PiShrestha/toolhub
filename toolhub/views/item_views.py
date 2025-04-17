from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ..forms import ItemForm
from ..models import Item, BorrowRequest

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

    return render(request, "toolhub/items/add_item.html", {"form": form})

@login_required
def edit_item(request, item_id):
    item = Item.objects.get(pk=item_id)
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can edit items.")

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ItemForm(instance=item)

    return render(request, "toolhub/items/edit_item.html", {"form": form, "item": item})

def tools_page(request):
    """Display all tools (items) with search functionality."""
    query = request.GET.get("q", "").strip()
    items = Item.objects.all()

    if query:
        items = items.filter(name__icontains=query)

    for item in items:
        item.already_requested = False
        if request.user.is_authenticated:
            item.already_requested = BorrowRequest.objects.filter(
                item=item,
                user=request.user,
                status__in=["pending", "approved"]
            ).exists()

    return render(request, "toolhub/items/tools_page.html", {"items": items, "query": query})