from datetime import timezone
from django import forms
from django.utils import timezone
from .models import CustomUser, Item, Collection, ItemReview, BorrowRequest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["profile_picture"]
        widgets = {
            "profile_picture": forms.FileInput(attrs={"class": "form-control-file"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "phone_number",
        ]
        widgets = {
            "profile_picture": forms.FileInput(attrs={"class": "form-control-file"}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if not user or user.role != "librarian":
            self.fields.pop("role", None)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "name",
            "identifier",
            "status",
            "location",
            "description",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "location": forms.Select(attrs={"class": "form-select"}),
        }


User = get_user_model()


class CollectionForm(forms.ModelForm):
    allowed_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(last_login__isnull=False),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Only applies to private collections.",
    )

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        widget=forms.MultipleHiddenInput,
        required=False
    )

    class Meta:
        model = Collection
        fields = ['title', 'description', 'visibility', 'image', 'items', 'allowed_users']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If bound data is present but no items/allowed_users, set as empty list.
        if self.data and "items" not in self.data:
            self.data = self.data.copy()
            self.data.setlist("items", [])
        if self.data and "allowed_users" not in self.data:
            self.data = self.data.copy()
            self.data.setlist("allowed_users", [])

    def clean(self):
        cleaned = super().clean()
        visibility = cleaned.get("visibility")
        items      = cleaned.get("items") or []   # <-- ensure iterable

        
        for item in items:
            other_private = item.collections.filter(
                visibility=Collection.PRIVATE
            ).exclude(pk=self.instance.pk)
            if other_private.exists():
                raise forms.ValidationError(
                    f"Item “{item.name}” is already in another private collection."
                )
        return cleaned


class ItemReviewForm(forms.ModelForm):
    class Meta:
        model = ItemReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "class": "form-control"}),
            "comment": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


class BorrowRequestForm(forms.ModelForm):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        label="Note (optional)"
    )

    class Meta:
        model = BorrowRequest
        fields = ["borrow_start_date", "return_due_date", "note"]
        widgets = {
            "borrow_start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "return_due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean_return_due_date(self):
        """
        Ensure the return due date is in the future.
        """
        return_due_date = self.cleaned_data.get("return_due_date")
        borrow_start_date = self.cleaned_data.get("borrow_start_date")
        if return_due_date and return_due_date <= timezone.localtime(timezone.now()).date():
            raise ValidationError("The return due date must be in the future.")
        if return_due_date <= borrow_start_date:
            raise ValidationError("The return due date after the borrow date.")
        return return_due_date

class PromoteUserForm(forms.Form):
    email = forms.EmailField(label="User Email", max_length=254)