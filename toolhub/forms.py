from django import forms
from .models import CustomUser, Item, Collection
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
        fields = ["name", "image"]
        widgets = {}


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
        instance = self.instance

        for item in items:
            private_collections = item.collections.filter(visibility=Collection.PRIVATE)

            if visibility == Collection.PRIVATE:
                if private_collections.exists() and instance not in private_collections:
                    raise ValidationError(
                        f"Item '{item.name}' is already in another private collection, and cannot be in any other collections."
                    )
            else:
                if private_collections.exists():
                    raise ValidationError(
                        f"Item '{item.name}' is already in another private collection, and cannot be in any other collections."
                    )

        return items
