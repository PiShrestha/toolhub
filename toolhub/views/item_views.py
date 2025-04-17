from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ..forms import ItemForm
from ..models import Item

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

@login_required
def tools_page(request):
    """Display all tools (items) with search functionality."""
    query = request.GET.get("q", "").strip()
    items = Item.objects.all()

    if query:
        items = items.filter(name__icontains=query)

    return render(request, "toolhub/items/tools_page.html", {"items": items, "query": query})