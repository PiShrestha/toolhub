from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from datetime import timedelta
from ..models import BorrowRequest, Item
from ..forms import BorrowRequestForm

@login_required
def request_borrow(request, item_id):
    """Handle borrow requests for an item."""
    item = get_object_or_404(Item, pk=item_id)

    # Check if the user already has a pending/approved request for this item.
    if BorrowRequest.objects.filter(
            item=item,
            user=request.user,
            status__in=["pending", "approved"],
    ).exists():
        messages.warning(request, "You already have an active borrow request for this item.")
        return redirect(request.META.get("HTTP_REFERER", "tools_page"))

    if request.method == "POST":
        form = BorrowRequestForm(request.POST)
        if form.is_valid():
            borrow_request = form.save(commit=False)
            borrow_request.item = item
            borrow_request.user = request.user
            borrow_request.save()

            # Remove or comment out the global update:
            # item.status = "currently_requested"
            # item.save()

            messages.success(request, f"Borrow request for '{item.name}' submitted successfully.")
            return redirect("home")
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
        messages.warning(request, f"Item '{item.name}' is already borrowed.")
    else:
        borrow_request.status = "approved"
        borrow_request.return_due_date = now().date() + timedelta(days=14)
        borrow_request.save()
        item.status = "currently_borrowed"
        item.borrower = borrow_request.user
        item.save()
        messages.success(request, f"Approved request and marked '{item.name}' as borrowed.")

    return redirect("my_borrow_requests")


@login_required
@require_POST
def deny_borrow(request, request_id):
    """Deny a borrow request and reset the item's status to available."""
    if request.user.role != "librarian":
        raise PermissionDenied("Only librarians can deny requests.")

    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if borrow_request.status != "pending":
        messages.warning(request, "Only pending requests can be denied.")
        return redirect("my_borrow_requests")

    # Set request status to denied
    borrow_request.status = "denied"
    borrow_request.save()

    # Reset the related item status to available if needed
    item = borrow_request.item
    if item.status in ["currently_requested"]:
        item.status = "available"
        item.save()

    messages.success(request, f"Denied borrow request for '{item.name}' and reset its status to available.")
    return redirect("my_borrow_requests")


@login_required
def borrow_overview(request):
    """
    Render a borrow overview page.
    
    Librarians see all borrow requests with approve/deny actions.
    Patrons see their own borrow requests (history) with an option to cancel pending requests.
    """
    if request.user.role == "librarian":
        # Get all borrow requests with related item and user
        borrow_requests = BorrowRequest.objects.select_related("item", "user").order_by("-request_date")
        template = "toolhub/borrow/borrow_requests.html"
    else:  # patron
        borrow_requests = BorrowRequest.objects.filter(user=request.user).order_by("-request_date")
        template = "toolhub/borrow/borrow_history.html"
    
    return render(request, template, {"borrow_requests": borrow_requests})


@login_required
def borrow_request_detail(request, request_id):
    """View details of a specific borrow request."""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    # Ensure only librarians or the user who made the request can view the details
    if request.user.role != "librarian" and request.user != borrow_request.user:
        raise PermissionDenied("You are not authorized to view this borrow request.")

    return render(request, "toolhub/borrow/borrow_request_detail.html", {"borrow_request": borrow_request})


@login_required
@require_POST
def cancel_borrow_request(request, request_id):
    """Cancel a pending borrow request."""
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if borrow_request.user != request.user:
        raise PermissionDenied("You are not authorized to cancel this borrow request.")

    if borrow_request.status != "pending":
        messages.warning(request, "Only pending borrow requests can be canceled.")
        return redirect("my_borrow_requests")

    borrow_request.delete()
    messages.success(request, "Your borrow request has been canceled successfully.")
    return redirect("my_borrow_requests")


@login_required
def return_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.borrower_id != request.user.id:
        raise PermissionDenied("You are not the borrower of this item.")

    if item.status == "currently_borrowed":
        # Mark the item as available and clear borrower
        item.status = "available"
        item.borrower = None
        item.save()

        # Find the most recent approved borrow request
        borrow_request = (
            BorrowRequest.objects
            .filter(item=item, user=request.user, status="approved")
            .order_by('-request_date')
            .first()
        )

        if borrow_request:
            today = now().date()
            due_date = borrow_request.return_due_date

            if due_date and today > due_date:
                borrow_request.status = "returned_overdue"
            else:
                borrow_request.status = "returned_on_time"

            borrow_request.save()

    return redirect('home')