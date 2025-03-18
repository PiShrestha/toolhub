from django import forms
from .models import CustomUser, Item

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["profile_picture"]
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_picture', 'phone_number', 'role']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "image"]
        widgets = {"image": forms.FileInput(attrs={"class": "form-control-file"})}