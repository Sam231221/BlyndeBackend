from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import Genre, User


class UserAdminForm(UserChangeForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class GenreAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = Genre
        fields = "__all__"
