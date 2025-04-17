from datetime import timezone
from django import forms
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
            "role",
        ]
        widgets = {
            "profile_picture": forms.FileInput(attrs={"class": "form-control-file"}),
        }


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

    class Meta:
        model = Collection
        fields = [
            "title",
            "description",
            "visibility",
            "items",
            "image",
            "allowed_users",
        ]
        widgets = {
            "items": forms.CheckboxSelectMultiple(),
        }

    def clean_items(self):
        items = self.cleaned_data.get("items")
        visibility = self.cleaned_data.get("visibility")
        instance = self.instance  # may be unsaved on create

        for item in items:
            private_collections = item.collections.filter(visibility=Collection.PRIVATE)
            public_collections = item.collections.filter(visibility=Collection.PUBLIC)

            if visibility == Collection.PRIVATE:
                if private_collections.exists():
                    if (
                        not instance.pk
                        or private_collections.exclude(pk=instance.pk).exists()
                    ):
                        raise ValidationError(
                            f"Item '{item.name}' is already in another private collection and cannot be reused."
                        )

            if visibility == Collection.PUBLIC:
                if private_collections.exists():
                    raise ValidationError(
                        f"Item '{item.name}' is already in a private collection and cannot be added to a public one."
                    )

            if visibility == Collection.PRIVATE:
                if public_collections.exists():
                    raise ValidationError(
                        f"Item '{item.name}' is already in a public collection and cannot be added to a private one."
                    )

        return items


class ItemReviewForm(forms.ModelForm):
    class Meta:
        model = ItemReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "class": "form-control"}),
            "comment": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


class BorrowRequestForm(forms.ModelForm):
    """
    Form for librarians to approve borrow requests by setting a return due date.
    """
    class Meta:
        model = BorrowRequest
        fields = ['return_due_date']
        widgets = {
            'return_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_return_due_date(self):
        """
        Ensure the return due date is in the future.
        """
        return_due_date = self.cleaned_data.get("return_due_date")
        if return_due_date and return_due_date <= timezone.now().date():
            raise ValidationError("The return due date must be in the future.")
        return return_due_date


class PromoteUserForm(forms.Form):
    email = forms.EmailField(label="User Email", max_length=254)