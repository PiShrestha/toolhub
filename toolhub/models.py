from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string
import uuid as uuid_lib

def upload_to_profile(instance, filename):
    extension = filename.split(".")[-1]
    return f"profile_pictures/{instance.email.replace('@', '_').replace('.', '_')}.{extension}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("patron", "Patron"),
        ("librarian", "Librarian"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patron")

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    profile_picture = models.ImageField(
        upload_to=upload_to_profile,
        storage=import_string(settings.DEFAULT_FILE_STORAGE)(),
        null=True,
        blank=True,
    )
    join_date = models.DateTimeField(auto_now_add=True)  # Records when the user joined

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                # If an old profile picture exists, is not the default, and has changed,
                # delete the old file from storage.
                if (
                    old_instance.profile_picture
                    and old_instance.profile_picture != self.profile_picture
                ):
                    if old_instance.profile_picture.name:
                        if default_storage.exists(old_instance.profile_picture.name):
                            default_storage.delete(old_instance.profile_picture.name)
            except CustomUser.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{self.profile_picture.name}"
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/default.png"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email


# Helper function for item and collection image uploads
def upload_to_item(instance, filename):
    extension = filename.split(".")[-1]
    return f"items/{instance.uuid}.{extension}"


class Item(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("currently_borrowed", "Currently Borrowed"),
        ("currently_requested", "Already Requested"),
        ("being_repaired", "Being Repaired"),
        ("lost", "Lost"),
        ("archived", "Archived"),
    ]

    LOCATION_CHOICES = [
        ("main_warehouse", "Main Warehouse"),
        ("aux_warehouse", "Aux Warehouse"),
        ("patrons_location", "Patron's Location"),
        ("remote_storage", "Remote Storage"),
    ]

    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    identifier = models.CharField(max_length=100, unique=True)

    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="available"
    )

    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items", blank=True, null=True
    )

    location = models.CharField(
        max_length=50, choices=LOCATION_CHOICES, default="main_warehouse"
    )

    image = models.ImageField(
        upload_to=upload_to_item,
        storage=import_string(settings.DEFAULT_FILE_STORAGE)(),
        blank=True,
        null=True,
    )

    @property
    def image_url(self):
        if self.image:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{self.image.name}"
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/logo.png"

    def __str__(self):
        return self.name

    def mark_as_borrowed(self):
        """
        Mark the item as currently borrowed.
        """
        if self.status != "available":
            raise ValidationError("Only available items can be borrowed.")
        self.status = "currently_borrowed"
        self.save()

    def mark_as_available(self):
        """
        Mark the item as available again.
        """
        if self.status != "currently_borrowed":
            raise ValidationError("Only borrowed items can be marked as available.")
        self.status = "available"
        self.save()


class Collection(models.Model):
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)

    PUBLIC = "public"
    PRIVATE = "private"

    VISIBILITY_CHOICES = [
        (PUBLIC, "Public"),
        (PRIVATE, "Private"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    items = models.ManyToManyField("Item", related_name="collections", blank=True)

    image = models.ImageField(
        upload_to=upload_to_item,
        storage=import_string(settings.DEFAULT_FILE_STORAGE)(),
        blank=True,
        null=True,
    )
    visibility = models.CharField(
        max_length=7, choices=VISIBILITY_CHOICES, default=PUBLIC
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections"
    )

    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="shared_collections",
        blank=True,
        help_text="Users who can access this private collection (librarians can always access).",
    )

    @property
    def image_url(self):
        if self.image:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{self.image.name}"
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/logo.png"

    def __str__(self):
        return self.title

    def clean(self):
        """
        Optional: Enforce that if a collection is private, an item in it should not belong to any other collection.
        You can decide whether to enforce this at the model level or handle it in your form/view.
        """
        if self.visibility == self.PRIVATE:
            for item in self.items.all():
                if item.collections.exclude(uuid=self.uuid).exists():
                    raise ValidationError(
                        f"Item '{item.title}' already belongs to another collection."
                    )


class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("returned_on_time", "Returned On Time"),
        ("returned_overdue", "Returned Late")
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="borrow_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrow_requests")
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    return_due_date = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    # Danny: Commented this out for the moment as it prevents a user from borrowing, returning, then borrowing the same item again
    # class Meta:
    #     unique_together = ("item", "user")  # Allow only one active request per user-item pair

    def __str__(self):
        return f"{self.user.email} - {self.item.name} ({self.status})"

    def approve(self, due_date):
        """
        Approve the borrow request, set the due date, and update the item's status.
        """
        if self.status != "pending":
            raise ValidationError("Only pending requests can be approved.")
        if not due_date:
            raise ValidationError("A due date must be set when approving a borrow request.")
        self.status = "approved"
        self.return_due_date = due_date
        self.item.mark_as_borrowed()
        self.save()

    def deny(self):
        """
        Deny the borrow request.
        """
        if self.status != "pending":
            raise ValidationError("Only pending requests can be denied.")
        self.status = "denied"
        self.save()


class ItemReview(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.item.title} by {self.user.email}"