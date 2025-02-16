# forms.py
from django import forms
from .models import Genre


class GenreAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = Genre
        fields = "__all__"
