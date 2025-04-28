from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from ..forms import ItemForm, ItemReviewForm
from ..models import Item, BorrowRequest
from django.views.decorators.http import require_POST
from django.contrib import messages

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
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect("home")

def tools_page(request):
    """Display all tools (items) with search functionality."""
    query = request.GET.get("q", "").strip()
    items = Item.objects.all()

    if query:
        items = items.filter(name__icontains=query)

    for item in items:
        item.already_requested = False
        if request.user.is_authenticated:
            item.user_status = item.status_for_user(request.user)
            item.already_requested = BorrowRequest.objects.filter(
                item=item,
                user=request.user,
                status__in=["pending", "approved"]
            ).exists()

    return render(request, "toolhub/items/tools_page.html", {"items": items, "query": query})

@login_required
def view_item(request, item_id):
    """Public / patron / librarian item detail with reviews & rating."""
    item = get_object_or_404(Item, pk=item_id)
    item.user_status = item.status_for_user(request.user)

    if request.method == "POST" and request.user.role == "patron":
        review_form = ItemReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user  = request.user
            review.item  = item
            review.save()
            messages.success(request, "Thanks for your review!")
            return redirect("view_item", item_id=item.id)
    else:
        review_form = ItemReviewForm()

    context = {
        "item": item,
        "reviews": item.reviews.select_related("user").order_by("-created_at"),
        "form": review_form,
    }
    return render(request, "toolhub/items/view_item.html", context)
