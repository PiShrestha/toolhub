from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from datetime import timedelta
from ..models import BorrowRequest, Item
from ..forms import BorrowRequestForm
from django.views.decorators.http import require_POST

@login_required
def request_borrow(request, item_id):
    """Handle borrow requests for an item."""
    item = get_object_or_404(Item, pk=item_id)

    if item.status != "available":
        messages.warning(request, f"Item '{item.title}' is not available for borrowing.")
        return redirect("profile")

    existing = BorrowRequest.objects.filter(
        item=item,
        user=request.user,
        status__in=["pending", "approved"]
    ).exists()
    if existing:
        messages.warning(request, "You already have an active borrow request for this item.")
        return redirect("profile")

    if request.method == "POST":
        form = BorrowRequestForm(request.POST)
        if form.is_valid():
            borrow_request = form.save(commit=False)
            borrow_request.item = item
            borrow_request.user = request.user
            borrow_request.save()
            messages.success(request, f"Borrow request for '{item.title}' submitted successfully.")
            return redirect("profile")
    else:
        form = BorrowRequestForm()

    return render(request, "toolhub/borrow/request_borrow.html", {"form": form, "item": item})


@login_required
@require_POST
def approve_borrow(request, request_id):
    """Approve a borrow request."""
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can approve requests.")

    borrow_request = get_object_or_404(BorrowRequest, id=request_id)
    item = borrow_request.item

    if item.status == "borrowed":
        messages.warning(request, f"Item '{item.title}' is already borrowed.")
    else:
        borrow_request.status = "approved"
        borrow_request.return_due_date = now().date() + timedelta(days=14)
        borrow_request.save()
        item.status = "borrowed"
        item.save()
        messages.success(request, f"Approved request and marked '{item.title}' as borrowed.")

    return redirect("librarian_borrow_requests")


@login_required
@require_POST
def deny_borrow(request, request_id):
    """Deny a borrow request."""
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can deny requests.")

    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if borrow_request.status != "pending":
        messages.warning(request, "Only pending requests can be denied.")
        return redirect("librarian_borrow_requests")

    borrow_request.status = "denied"
    borrow_request.save()
    messages.success(request, f"Denied borrow request for '{borrow_request.item.title}'.")
    return redirect("librarian_borrow_requests")


@login_required
def librarian_borrow_requests(request):
    """View all pending borrow requests (for librarians)."""
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can view this page.")

    requests = BorrowRequest.objects.filter(status="pending").select_related("item", "user").order_by("-request_date")
    return render(request, "toolhub/borrow/librarian_borrow_requests.html", {"requests": requests})


@login_required
def borrow_request_detail(request, request_id):
    """View details of a specific borrow request."""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    # Ensure only librarians or the user who made the request can view the details
    if request.user.role != "librarian" and request.user != borrow_request.user:
        raise PermissionDenied("You are not authorized to view this borrow request.")

    return render(request, "toolhub/borrow/borrow_request_detail.html", {"borrow_request": borrow_request})


@login_required
def borrow_history(request):
    """View borrow history for the logged-in patron."""
    if request.user.role != "patron":
        raise PermissionDenied("Only patrons can view their borrow history.")

    borrow_requests = BorrowRequest.objects.filter(user=request.user).order_by("-request_date")
    return render(request, "toolhub/borrow/borrow_history.html", {"borrow_requests": borrow_requests})


@login_required
@require_POST
def cancel_borrow_request(request, request_id):
    """Cancel a pending borrow request."""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if borrow_request.user != request.user:
        raise PermissionDenied("You are not authorized to cancel this borrow request.")

    if borrow_request.status != "pending":
        messages.warning(request, "Only pending borrow requests can be canceled.")
        return redirect("borrow_history")

    borrow_request.delete()
    messages.success(request, "Your borrow request has been canceled successfully.")
    return redirect("borrow_history")